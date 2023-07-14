from cassandra.cluster import Cluster
from langchain.prompts import load_prompt
from langchain.document_loaders import ConfluenceLoader
from langchain.vectorstores.cassandra import Cassandra
from langchain.indexes import VectorstoreIndexCreator
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from cassandra.auth import PlainTextAuthProvider
from langchain.docstore.document import Document
from langchain.document_loaders import TextLoader
import os
from langchain.llms import VertexAI
from langchain.embeddings import VertexAIEmbeddings

CONFLUENCE_URL = os.environ.get("CONFLUENCE_URL")
#https://confluence.atlassian.com/enterprise/using-personal-access-tokens-1026032365.html
CONFLUENCE_TOKEN = os.environ.get("CONFLUENCE_TOKEN")

#https://awesome-astra.github.io/docs/pages/astra/download-scb/#c-procedure
ASTRADB_TOKEN = os.environ.get("ASTRADB_TOKEN")
ASTRADB_BUNDLE = os.environ.get("ASTRADB_BUNDLE")
ASTRADB_KEYSPACE = os.environ.get("ASTRADB_KEYSPACE")
ASTRADB_TABLE = os.environ.get("ASTRADB_TABLE")
GOOGLE_APPLICATION_CREDENTIALS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")

session = None

def get_cassandra_session():
    global session
    cloud_config= {
        'secure_connect_bundle': ASTRADB_BUNDLE
    }
    auth_provider = PlainTextAuthProvider('token', ASTRADB_TOKEN)
    cluster = Cluster(cloud=cloud_config, auth_provider=auth_provider, connect_timeout=60 )
    session = cluster.connect()

get_cassandra_session()
llm = VertexAI()
embedding= VertexAIEmbeddings()

#for testing without confluece
#loader = TextLoader('amontillado.txt', encoding='utf8')
#documents = loader.load()

loader = ConfluenceLoader(url=CONFLUENCE_URL, token=CONFLUENCE_TOKEN)
documents = loader.load(
    space_key="SPACE", include_attachments=True, limit=50, max_pages=50
)

index_creator = VectorstoreIndexCreator(
    vectorstore_cls=Cassandra,
    embedding=embedding,
    text_splitter=CharacterTextSplitter(
        chunk_size=400,
        chunk_overlap=0,
    ),
    vectorstore_kwargs={
        'session': session,
        'keyspace': ASTRADB_KEYSPACE,
        'table_name': ASTRADB_TABLE,
    },
)
index = index_creator.from_loaders([loader])

template = """
api: llm  
params:
  prompt: |
    {query}
  temperature: 0
  max_tokens: 50
result_key: llm_result
"""
user_question = "What hooks do we have for custom sstable implementations?"
user_context = "Has been using cassandra since v0.8, is a committer on the project."


#If you don't have custom prompt templates just do this:
#result = index.query_with_sources(user_question, llm=llm)
#print(result)

vector_search_results = index.vectorstore.search(query=user_question, search_type="similarity")

#template_path = "./templates/learner.yaml"
template_path = "./templates/qualified.yaml"
prompt_template = load_prompt(template_path)

prompt = prompt_template.format(**{"user_question": user_question, "user_context": user_context, "vector_search_results": vector_search_results})

result = llm(prompt)
print(result)
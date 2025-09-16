from neo4j import GraphDatabase
import os
from typing import Dict, List

class KnowledgeGraph:
    def __init__(self):
        uri = os.environ.get("NEO4J_URI", "bolt://neo4j:7687")
        auth = (os.environ.get("NEO4J_USER", "neo4j"), os.environ.get("NEO4J_PASSWORD", "test1234"))
        self.driver = GraphDatabase.driver(uri, auth=auth)

    def close(self):
        self.driver.close()

    def upsert_entities_relations(self, entities: List[Dict], relations: List[Dict]):
        cypher_entities = """
        UNWIND $entities AS e
        MERGE (n:Entity {id: e.id})
        SET n += e
        """
        cypher_relations = """
        UNWIND $rels AS r
        MATCH (a:Entity {id: r.source}), (b:Entity {id: r.target})
        MERGE (a)-[rel:RELATION {type: r.type}]->(b)
        SET rel += r
        """
        with self.driver.session() as session:
            if entities:
                session.run(cypher_entities, entities=entities)
            if relations:
                session.run(cypher_relations, rels=relations)



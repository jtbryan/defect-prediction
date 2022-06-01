#!/usr/bin/env python

import json
from neo4j import GraphDatabase
from tqdm import tqdm
import config

class NeoDriver:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def update_dev_exp(self, name, exp):
        with self.driver.session() as session:
            session.write_transaction(self._update_dev_exp, name, exp)

    @staticmethod
    def _update_dev_exp(tx, name, exp):
        result = tx.run("MATCH (d:Developer) "
                        "WHERE d.name = $name "
                        "SET d.experience = $exp "
                        "RETURN *", name=name, exp=exp)
        return result

def main():

    driver = NeoDriver("bolt://localhost:7687", "neo4j", config.neo4j_pass)

    with open('../data_assembler/results/author_graph.json') as f:  
        data = json.load(f)

    for _, dev in enumerate(tqdm(data)):
        last_commit = list(data[dev])[-1]
        experience = data[dev][last_commit]['exp']
        driver.update_dev_exp(dev, experience)

    driver.close()

if __name__ == "__main__":
    main()
    
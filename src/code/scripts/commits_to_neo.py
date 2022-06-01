#!/usr/bin/env python

import git
from git import exc 
from pygit2 import Repository
import pandas as pd
import argparse
import json
import config
from neo4j import GraphDatabase
from tqdm import tqdm
from datetime import datetime
import csv

class NeoDriver:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_repo(self, repo):
        with self.driver.session() as session:
            print("Creating repo node...")
            session.write_transaction(self._create_repo_node, repo)

    def create_folder(self, folder):
        with self.driver.session() as session:
            session.write_transaction(self._create_folder_node, folder)

    def create_file(self, file):
        with self.driver.session() as session:
            session.write_transaction(self._create_file_node, file)
    
    def create_person(self, developer, id):
        with self.driver.session() as session:
            #print("Creating person node...")
            session.write_transaction(self._create_person_node, developer, id)

    def create_commit(self, commit, commit_type, commit_time):
        with self.driver.session() as session:
            #print("Creating commit node...")
            session.write_transaction(self._create_commit_node, commit, commit_type, commit_time)

    def create_fix_intoduce(self, bf_commit, bi_commit):
        with self.driver.session() as session:
            session.write_transaction(self._create_fix_to_introduce, bf_commit, bi_commit)

    def create_person_to_commit(self, commit, commit_type, person_name):
        with self.driver.session() as session:
            #print("Creating relationship between commit and person nodes...")
            session.write_transaction(self._create_relations_person_commit, commit, commit_type, person_name)

    def create_person_to_repo(self, name, commit_type, hexsha, date):
        with self.driver.session() as session:
            session.write_transaction(self._create_person_to_repo, name, commit_type, hexsha, date)

    def create_person_to_folder(self, name, folder_name, commit_type, hexsha, date):
        with self.driver.session() as session:
            session.write_transaction(self._create_person_to_folder, name, folder_name, commit_type, hexsha, date)

    def create_person_to_file(self, name, file_name, commit_type, hexsha, date):
        with self.driver.session() as session:
            session.write_transaction(self._create_person_to_file, name, file_name, commit_type, hexsha, date)

    def create_person_bug_to_folder(self, name, folder_name, commit_type, hexsha, date):
        with self.driver.session() as session:
            session.write_transaction(self._create_person_bug_to_folder, name, folder_name, commit_type, hexsha, date)

    def create_person_bug_to_file(self, name, file_name, commit_type, hexsha, date):
        with self.driver.session() as session:
            session.write_transaction(self._create_person_bug_to_file, name, file_name, commit_type, hexsha, date)

    def create_relations(self):
        with self.driver.session() as session:
            session.write_transaction(self._create_relations_between_nodes)

    def delete_all(self):
        with self.driver.session() as session:
            print("Deleting all nodes...")
            session.write_transaction(self._delete_nodes_and_relationships)

    def create_one_mode_projection(self):
        with self.driver.session() as session:
            print("Creating one mode projection...")
            session.write_transaction(self._create_one_mode_projection)

    def pagerank(self):
        with self.driver.session() as session:
            session.write_transaction(self._pagerank)

    def betweenness(self):
        with self.driver.session() as session:
            session.write_transaction(self._betweenness)

    def closeness(self):
        with self.driver.session() as session:
            session.write_transaction(self._closeness)

    def harmonic(self):
        with self.driver.session() as session:
            session.write_transaction(self._harmonic)

    def degree(self):
        with self.driver.session() as session:
            session.write_transaction(self._degree)

    def louvain(self):
        with self.driver.session() as session:
            session.write_transaction(self._louvain)

    def node2vec(self):
        with self.driver.session() as session:
            session.write_transaction(self._node2vec)

    def get_results(self, outfile):
        with self.driver.session() as session:
            res = session.read_transaction(self._get_results)
            with open(outfile, "w", newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Name", "File", "Bug", "PageRank", "Betweenness", "Closeness", "Harmonic", "Degree", "communityId", "n2vEmbedding"])
                for item in res:
                    writer.writerow(item)

    def drop_projection(self):
        with self.driver.session() as session:
            session.write_transaction(self._drop_projection)

    @staticmethod
    def _create_repo_node(tx, repo):
        result = tx.run("CREATE (r:Repo) "
                        "SET r.repoName = $repo "
                        "RETURN r.repoName + ', from node ' + id(r)", repo=repo)
        return result

    @staticmethod
    def _create_folder_node(tx, folder):
        tx.run("CREATE (f:Folder) "
               "SET f.folderName = $folder "
               "RETURN * ", folder=folder)

    @staticmethod
    def _create_file_node(tx, file):
        tx.run("CREATE (f:File) "
               "SET f.fileName = $file; ", file=file)

    @staticmethod
    def _create_person_node(tx, developer, id):
        result = tx.run("CREATE (p:Developer) " 
                        "SET p.name = {name} " 
                        "SET p.email = {email} "
                        "SET p.uniqid = {id} "
                        "RETURN p.name + ', from node ' + id(p); ".format(name=repr(developer[0]), email=repr(developer[1]), id=id))
        return result

    @staticmethod
    def _create_commit_node(tx, commit, commit_type, commit_time):
        tx.run("CREATE (c:Commit_{commit_type}) "
                "SET c.hex = {hexsha} "
                "SET c.time = datetime({commit_time}); ".format(commit_type=commit_type, hexsha=repr(commit), commit_time=repr(str(commit_time).replace(' ', 'T'))))

        tx.run("MATCH (r:Repo) "
               "MATCH (c:Commit_{commit_type}) "
               "WHERE c.hex = {hexsha} "
               "CREATE (c)-[:PUSHED_{commit_type_name}_TO]->(r); ".format(commit_type=commit_type, hexsha=repr(commit), commit_type_name=commit_type.upper()))

    @staticmethod
    def _create_fix_to_introduce(tx, bf_commit, bi_commit):
        tx.run("MATCH (c1:Commit_bf) "
               "MATCH (c2:Commit_bi) "
               "WHERE c1.hex = {hexsha1} AND c2.hex = {hexsha2} "
               "CREATE (c1)-[:FIXES]->(c2); ".format(hexsha1=repr(bf_commit), hexsha2=repr(bi_commit)))

    @staticmethod
    def _create_person_to_repo(tx, person_name, commit_type, hexsha, date):
        tx.run("MATCH (p:Developer) "
               "MATCH (r:Repo) "
               "WHERE p.name = {name} "
               "CREATE (p)-[:INTRODUCED_{bug_string} {{commit_hex: {hexsha}, commit_datetime: datetime({date})}}]->(r); ".format(name=repr(person_name), bug_string=commit_type, hexsha=repr(hexsha), date=repr(str(date).replace(' ', 'T'))))

    @staticmethod
    def _create_person_to_folder(tx, person_name, folder_name, commit_type, hexsha, date):
        tx.run("MATCH (p:Developer) "
               "MATCH (f:Folder) "
               "WHERE p.name = {name} AND f.folderName = {folder_name}"
               "CREATE (p)-[:INTRODUCED_{bug_string} {{commit_hex: {hexsha}, commit_datetime: datetime({date})}}]->(f); ".format(name=repr(person_name), folder_name=repr(folder_name), bug_string=commit_type, hexsha=repr(hexsha), date=repr(str(date).replace(' ', 'T'))))

    @staticmethod
    def _create_person_to_file(tx, person_name, file_name, commit_type, hexsha, date):
        tx.run("MATCH (p:Developer) "
               "MATCH (f:File) "
               "WHERE p.name = {name} AND f.fileName = {file_name}"
               "CREATE (p)-[:INTRODUCED_{bug_string} {{commit_hex: {hexsha}, commit_datetime: datetime({date})}}]->(f); ".format(name=repr(person_name), file_name=repr(file_name), bug_string=commit_type, hexsha=repr(hexsha), date=repr(str(date).replace(' ', 'T'))))
               
    @staticmethod
    def _create_person_bug_to_folder(tx, person_name, folder_name, commit_type, hexsha, date):
        tx.run("MATCH (p:Developer)-[rel:INTRODUCED_NORMAL_COMMIT]->(f:Folder) "
               "WHERE rel.commit_hex = {hexsha}"
               "MERGE (p)-[:INTRODUCED_{bug_string} {{commit_hex: {hexsha}, commit_datetime: datetime({date})}}]->(f) "
               "DELETE rel; ".format(name=repr(person_name), folder_name=repr(folder_name), bug_string=commit_type, hexsha=repr(hexsha), date=repr(str(date).replace(' ', 'T'))))
    
    @staticmethod
    def _create_person_bug_to_file(tx, person_name, file_name, commit_type, hexsha, date):
        tx.run("MATCH (p:Developer)-[rel:INTRODUCED_NORMAL_COMMIT]->(f:File) "
               "WHERE rel.commit_hex = {hexsha}"
               "MERGE (p)-[:INTRODUCED_{bug_string} {{commit_hex: {hexsha}, commit_datetime: datetime({date})}}]->(f) "
               "DELETE rel; ".format(name=repr(person_name), file_name=repr(file_name), bug_string=commit_type, hexsha=repr(hexsha), date=repr(str(date).replace(' ', 'T'))))
               
    @staticmethod
    def _create_relations_person_commit(tx, commit, commit_type, person_name):
        tx.run("MATCH (c:Commit_{commit_type}) "
               "MATCH (p:Developer) "
               "WHERE c.hex = {hexsha} AND p.name = {name} "
               "CREATE (p)-[:CREATED]->(c); ".format(commit_type=commit_type, hexsha=repr(commit), name=(repr(person_name))))

    @staticmethod
    def _create_relations_between_nodes(tx):
        tx.run("MATCH (p:Developer) "
                "MATCH (r:Repo) "
                "CREATE (p)-[:INTRODUCED_BUG_FIX]->(r); ")
        tx.run("MATCH (p:Developer) "
                "MATCH (r:Repo) "
                "CREATE (p)-[:INTRODUCED_NEW_BUG]->(r); ")
        tx.run("MATCH (p:Developer) "
                "MATCH (r:Repo) "
                "CREATE (p)-[:CREATED_AND_FIXED_BUGS]->(r); ")

    @staticmethod
    def _delete_nodes_and_relationships(tx):
        tx.run("MATCH (n) "
               "DETACH DELETE n ")

    # Create one-mode projection
    @staticmethod
    def _create_one_mode_projection(tx):
        tx.run("""CALL gds.graph.create.cypher('my-graph',"""
               """'MATCH (p:Developer) RETURN id(p) as id, labels(p) AS labels, p.uniqid as uid',"""
               """'MATCH (p1:Developer)-[re]->(f:File)<-[re2]-(p2:Developer) WHERE p1.uniqid <> p2.uniqid RETURN id(p1) AS source, id(p2) AS target, "CONTRIBUTED_WITH" as type, count(distinct re) as weight, date(re.commit_datetime).year as year')""")

    # Topographic Metrics
    @staticmethod
    def _pagerank(tx):
        tx.run("CALL gds.pageRank.stream('my-graph', {maxIterations: 20,dampingFactor: 0.85,relationshipWeightProperty: 'weight'})"
               " YIELD nodeId, score"
               " MATCH (p:Developer)"
               " WHERE id(p) = nodeId"
               " SET p.PRScore = score"
               " RETURN gds.util.asNode(nodeId).name as name, score"
               " ORDER BY score desc")

    @staticmethod
    def _betweenness(tx):
        tx.run("CALL gds.betweenness.stream('my-graph')"
               " YIELD nodeId, score"
               " MATCH (p:Developer)"
               " WHERE id(p) = nodeId"
               " SET p.BetweenScore = score"
               " RETURN p.name, score"
               " ORDER BY score desc ")

    @staticmethod
    def _closeness(tx):
        tx.run("CALL gds.alpha.closeness.stream('my-graph')"
               " YIELD nodeId, centrality"
               " MATCH (p:Developer)"
               " WHERE id(p) = nodeId"
               " SET p.ClosenessScore = centrality"
               " RETURN p.name, centrality"
               " ORDER BY centrality desc")

    @staticmethod
    def _harmonic(tx):
        tx.run("CALL gds.alpha.closeness.harmonic.stream('my-graph')"
               " YIELD nodeId, centrality"
               " MATCH (p:Developer)"
               " WHERE id(p) = nodeId"
               " SET p.HarmonicScore = centrality"
               " RETURN p.name, centrality"
               " ORDER BY centrality desc")

    @staticmethod
    def _degree(tx):
        tx.run("CALL gds.alpha.degree.stream('my-graph', {relationshipWeightProperty: 'weight'})"
               " YIELD nodeId, score"
               " MATCH (p:Developer)"
               " WHERE id(p) = nodeId"
               " SET p.DegreeScore = score"
               " RETURN p.name, score"
               " ORDER BY score desc")    

    # Community Metrics
    @staticmethod
    def _louvain(tx):
        tx.run("CALL gds.louvain.stream('my-graph')"
               " YIELD nodeId, communityId"
               " MATCH (p:Developer)"
               " WHERE id(p) = nodeId"
               " SET p.communityId = communityId"
               " RETURN p.name, communityId"
               " ORDER BY communityId desc") 

    @staticmethod
    def _node2vec(tx):
        tx.run("CALL gds.alpha.node2vec.stream('my-graph')"
               " YIELD nodeId, embedding"
               " MATCH (p:Developer)"
               " WHERE gds.util.asNode(nodeId).name = p.name"
               " SET p.embedding = embedding"
               " RETURN *") 

    @staticmethod
    def _get_results(tx):
        items = []
        result = tx.run("MATCH (p:Developer)-[re]->(f:File)"
               " RETURN p.name as Name, f.fileName as File, type(re) as Bug, p.PRScore as PageRank, p.BetweenScore as Betweenness, p.ClosenessScore as Closeness, p.HarmonicScore as Harmonic, p.DegreeScore as Degree, p.communityId as communityId, p.embedding as n2vEmbedding") 

        for item in result:
            items.append([item['Name'], item['File'], item['Bug'], item['PageRank'], item['Betweenness'], item['Closeness'], item['Harmonic'], item['Degree'], item['communityId'], item['n2vEmbedding']])
        return items

    @staticmethod
    def _drop_projection(tx):
        tx.run("CALL gds.graph.drop('my-graph')")

def get_repo_name(repo_path):

    repo_name = ''

    if repo_path.find('\\'):
        temp = repo_path.split('\\')
        if temp[-1] == '':
            repo_name = temp[-2]
        else:
            repo_name = temp[-1]
    elif repo_path.find('/'):
        temp = repo_path.split('/')
        if temp[-1] == '':
            repo_name = temp[-2]
        else:
            repo_name = temp[-1]

    return repo_name

def populate_neo(repo_path, fip, outfile="temp.csv"):

    #NOTE: Modify the localhost port number if necessary, also ensure that you have a config.py containing your neo4j pass
    driver = NeoDriver("bolt://localhost:7687", "neo4j", config.neo4j_pass)
    driver.delete_all() # refresh the database

    #NOTE: Uncomment these lines to create a repo node
    #repo_name = get_repo_name(repo_path)
    #driver.create_repo(repo_name)

    repo = git.Repo(repo_path)

    json_objs = None
    with open(fip) as f:
        json_objs = json.load(f)

    commits = list()

    #NOTE: change main to whatever branch you would like to collect commits from
    for branch in Repository(repo_path).branches:
        # main = Repository(repo_path).head.shorthand
        commits.extend(list(repo.iter_commits(branch)))

    commit_dict = {}
    #all_folders = set()
    all_files = set()
    checked = set() # used to ignore duplicate pairs
    seen_commits = set() # used to create only one connection
    authors = {}
    
    print("Creating file nodes & developers...")
    for i, commit in enumerate(tqdm(commits)):
        commit_dict[commit.hexsha] = commit
        if commit.author.name not in authors:
            name = commit.author.name.replace("\\", "")
            authors[name] = (name, commit.author.email)
            driver.create_person(authors[name], i) 
        for modified_file in commit.stats.files:
            if modified_file not in all_files:
                all_files.add(modified_file)
                driver.create_file(modified_file)
            driver.create_person_to_file(commit.author.name, modified_file, "NORMAL_COMMIT", commit.hexsha, commit.committed_datetime)

    print("Creating bug fix & bug introduce relationships...")
    for _, pair in enumerate(tqdm(json_objs)):
        # check for duplicate pairs
        if tuple(pair) in checked:
            continue      
        else:
            checked.add(tuple(pair))
        try:
            # TODO: Ocassionally there may be issues that were found on other branches, but not successfully merged into master.
            bf_author = commit_dict[pair[0]].author
            bi_author = commit_dict[pair[1]].author

            # get bug-fixing commit
            if pair[0] not in seen_commits:
                seen_commits.add(pair[0])
                for modified_file in commit_dict[pair[0]].stats.files:
                    driver.create_person_bug_to_file(bf_author.name, modified_file, "BUG_FIX", commit_dict[pair[0]].hexsha, commit_dict[pair[0]].committed_datetime)

            # get bug-introducing commit
            if pair[1] not in seen_commits:
                seen_commits.add(pair[1])
                for modified_file in commit_dict[pair[1]].stats.files:
                    driver.create_person_bug_to_file(bi_author.name, modified_file, "NEW_BUG", commit_dict[pair[1]].hexsha, commit_dict[pair[1]].committed_datetime)
        except Exception as e:
            print(f"Failed to retrieve: {e}, may be on another branch")
    
    driver.create_one_mode_projection()
    print("Getting topographic metrics...")
    driver.pagerank()
    driver.betweenness()
    driver.closeness()
    driver.harmonic()
    driver.degree()
    print("Getting community metrics...")
    driver.louvain()
    driver.node2vec()

    driver.get_results(outfile)

    driver.drop_projection()

    print("Task completed")

    driver.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Given the results from SZZUnleashed, create a CSV file containing users that either introduce a bug-fixing commit or bug-introducing commit')
    parser.add_argument('--repo_path', type=str, required=True,
                    help='The relative or absolute path to the cloned repository.')
    parser.add_argument('--fip', type=str, required=True,
                    help='The path to the JSON file containing the "fix and introducer pairs" from SZZUnleashed.')
    parser.add_argument('--outfile', type=str,
                    help='Output file name.')
    

    args = parser.parse_args()

    if args.outfile:
        populate_neo(args.repo_path, args.fip, args.outfile)
    else:
        populate_neo(args.repo_path, args.fip)

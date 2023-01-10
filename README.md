# defect-prediction

Using graph-based ML for detecting defect-introducing commits early in open source projects.

## Purpose

Prior research has shown that it is possible to analyze open source repositories and determine what commits have fixed a known bug, as well as what commits are likely candidates for having introduced the bug originally. This is done primarily through the **SZZ Algorithm** introduced by Jacek Sliwerski, Thomas Zimmerman, and Andreas Zeller. By utilizing [SZZ Unleashed](https://github.com/wogscpar/SZZUnleashed), a Java implementation of the SZZ algorithm, we hope to illustrate the graph of interactions between developers contributing to these open source repositories by using [Neo4j](https://neo4j.com/) and Graph-Based machine learning. In doing so, we hope to effectively improve early detection of defect-introducing commits into these repositories. 

## Requirements

* ``Java 8`` is **required** for SZZUnleashed. [View the README](./src/code/README.md).
* ``Gradle`` is **required** for SZZUnleashed.
* ``Python 3`` is required to run the necessary scripts for this prject
    * Any necessary modules required for these scripts can be found in the ``requirements.txt`` [here](./requirements.txt). Simply run the following command: ``python -m pip install -r requirements.txt``
* The creation of a ``config.py`` file in the ``./src/code/scripts`` folder containing both a github API key, as well as the password for your respective Neo4j server. The format for this file may look like the following:
```python
api_key="Github_API_key"
neo4j_pass="Neo4j_Password"
```

## Usage
###  Data Collection & SZZ Usage
1. Collect issues associated with an open source github repository using ``fetch_issues.py`` [here](./src/code/scripts/fetch_issues.py)
    * Usage for this file can be found in the [README](./src/code/scripts/README.md)
    * This script utilizes the Github API key. Usage without this API key will require modification of this script.
2. Collect commits associated with an open source github repository using ``fetch_commits.py`` [here](./src/code/scripts/fetch_commits.py)
    * Usage for this file can be found in the [README](./src/code/scripts/README.md)
    * This script requires a cloned copy of the repository 
3. Find bug fixes using ``find_bug_fixes.py`` [here](./src/code/scripts/find_bug_fixes.py)
    * Usage for this file can be found in the [README](./src/code/examples/FindBugFixes.md)
4. Utilize the SZZUNleashed implementation of the SZZ Algorithm [here](./src/code/szz) using the command ``gradle build && gradle fatJar``
5. Run the resulting JAR file from the previous step using the command: ``java -jar build/libs/szz_find_bug_introducers-0.1.jar -i <issue_list> -r <repo>``
    * This will output three separate files, ``annotations.json``, ``commits.json``, ``fix_and_introducers_pairs.json``
6. After collecting the data resulting from the SZZUnleashed algorithm, you can then populate the Neo4j database using the ``commits_to_neo.py`` script [here](./src/code/scripts/commits_to_neo.py)

#### Developer Metrics
* **Experience**
    1. Run ``cd src/code/data_assembler``
    2. Run ``python .\assemble_experience_features.py -r <cloned repository path> -sg -b <branch name>`` which will creates both the ``author_graph.json`` and ``experience_features.csv`` files.
    3. To update these results in Neo4j, first start your database and then use the following command: ``python src/code/scripts/update_dev_exp.py``

### Neo4j Commands

#### Centrality metrics


* Create the **one-mode projection** first 
     ```
    CALL gds.graph.create.cypher('my-graph', 
    'MATCH (p:Developer) RETURN id(p) as id, labels(p) AS labels, p.uniqid as uid', 
    'MATCH (p1:Developer)-[re]->(f:File)<-[re2]-(p2:Developer) WHERE p1.uniqid <> p2.uniqid RETURN id(p1) AS source, id(p2) AS target, "CONTRIBUTED_WITH" as type, count(distinct re) as weight, date(re.commit_datetime).year as year')
  ```

* Call Page Rank on new graph:
    ```
    CALL gds.pageRank.stream('my-graph', {
    maxIterations: 20,
    dampingFactor: 0.85,
    relationshipWeightProperty: 'weight'})
    YIELD nodeId, score
    MATCH (p:Developer)
    WHERE id(p) = nodeId
    SET p.PRScore = score
    RETURN gds.util.asNode(nodeId).name as name, score
    ORDER BY score desc
    ```

* For betweenness:
    ```
    CALL gds.betweenness.stream('my-graph')
    YIELD nodeId, score
    MATCH (p:Developer)
    WHERE id(p) = nodeId
    SET p.BetweenScore = score
    RETURN p.name, score
    ORDER BY score desc 
    ```

* For closeness:
    ```
    CALL gds.alpha.closeness.stream('my-graph')
    YIELD nodeId, centrality
    MATCH (p:Developer)
    WHERE id(p) = nodeId
    SET p.ClosenessScore = centrality
    RETURN p.name, centrality
    ORDER BY centrality desc
    ```

* For harmonic:
    ```
    CALL gds.alpha.closeness.harmonic.stream('my-graph')
    YIELD nodeId, centrality
    MATCH (p:Developer)
    WHERE id(p) = nodeId
    SET p.HarmonicScore = centrality
    RETURN p.name, centrality
    ORDER BY centrality desc
    ```

* For degree:
    ```
    CALL gds.alpha.degree.stream('my-graph', {relationshipWeightProperty: 'weight'})
    YIELD nodeId, score
    MATCH (p:Developer)
    WHERE id(p) = nodeId
    SET p.DegreeScore = score
    RETURN p.name, score
    ORDER BY score desc
    ```

#### Community Metrics

* For Louvain community:
    ```
    CALL gds.louvain.stream('my-graph')
    YIELD nodeId, communityId
    MATCH (p:Developer) 
    WHERE id(p) = nodeId
    SET p.communityId = communityId
    RETURN p.name, communityId
    ORDER BY communityId desc;
    ```

* For Node2Vec embeddings:
    ```
    CALL gds.alpha.node2vec.stream('my-graph')
    YIELD nodeId, embedding
    MATCH (p:Developer)
    WHERE gds.util.asNode(nodeId).name = p.name
    SET p.embedding = embedding
    RETURN *
    ```

#### Output results

*
    ```
    MATCH (p:Developer)-[re]->(f:File)
    RETURN p.name as Name, f.fileName as File, type(re) as Bug, p.PRScore as PageRank, p.BetweenScore as Betweenness, p.ClosenessScore as Closeness, p.HarmonicScore as Harmonic, p.DegreeScore as Degree, p.communityId as communityId, p.embedding as n2vEmbedding
    ```
import networkx as nx
from analyzers import CommentMetaAnalysis
from textsim import cosine_sim
from models import CommentNode, AuthorNode, Node, ArticleNode, SentimentNode
from base import RedditBot
import mapper_functions as mp
import neonx


def load_graph(filepath, type):
    """
        :type filepath: str
        :rtype Graph
    """
    return nx.read_graphml(filepath, node_type=type)


class GraphBot(RedditBot):
    """
        builds graph
    """

    @property
    def main_graph(self):
        if self._main_graph == None:
            raise Exception("You have to call getGraph(*ids) first")

        return self.main_graph

    @property
    def comment_graph(self):
        if self._main_graph == None:
            raise Exception("You have to call getGraph(*ids) first")

        return self._comment_graph

    @main_graph.setter
    def main_graph(self, value):
        self._main_graph = value

    @comment_graph.setter
    def comment_graph(self, value):
        self._comment_graph = value

    def __init__(self, subreddit, username="CleverChuk", password="BwO9pJdzGaVj2pyhZ4kJ"):
        self._ids = None
        super().__init__(subreddit, username, password)

        self._main_graph = None
        self._comment_graph = None

    def stream(self, subreddit):
        """
            streams graphs from the given subreddit 
        """
        stream = self.reddit.subreddit(subreddit).stream
        for submission in stream.submissions():
            yield self.getGraph(submission.id)

    def getGraph(self, *ids):
        """"
            builds graph from article with submission id
        """
        self._ids = ids  # save the ids for future queries
        sentiment = {"Positive": SentimentNode("Positive"), "Negative": SentimentNode(
            "Negative"), "Neutral": SentimentNode("Neutral")}
        articleCommentEdges = []  # article/comment edge
        commentCommentEdges = []  # undirected comment/comment edges

        sentimentCommentEdges = []  # sentiment/comment edges
        authorCommentsEdges = []  # author/comment edges
        nodes = []

        # create a digraph for comment/comment edges
        diGraph = nx.DiGraph()
        # create a graph object
        graph = nx.Graph()

        # add the sentiment nodes to the node list
        for _, v in sentiment.items():
            nodes.append((v, v.__dict__))

        for id in ids:
            try:
                submission = self.get_submission(id)
                submission.comments.replace_more(limit=None)
                articleNode = ArticleNode(submission)
                nodes.append((articleNode, articleNode.__dict__))

                # populate article/comment edge list
                for comment in submission.comments.list():
                    commentNode = CommentNode(
                        comment, CommentMetaAnalysis(comment))
                    articleCommentEdges.append(
                        (commentNode, articleNode, {"type": "article-comment"}))

                    authorNode = AuthorNode(commentNode.author)
                    authorCommentsEdges.append(
                        (authorNode, commentNode, {"type": "author-comment"}))

                    nodes.append((authorNode, authorNode.__dict__))
                    nodes.append((commentNode, commentNode.__dict__))
                    diGraph.add_nodes_from([(commentNode, commentNode.__dict__)])

                
            except Exception as pe:
                print(pe)

        # populate sentiment/comment  and comment/comment edge list
        for p_comment, _,  *_ in articleCommentEdges:
            sentimentCommentEdges.append((sentiment[p_comment.sentiment], p_comment, {
                "score": p_comment.sentimentScore, "type": "SENTIMENT"}))

            for c_comment, _,  *_ in articleCommentEdges:
                if c_comment.parent_id == p_comment.id:
                    # nx does not support numpy float
                    c_comment.similarity = round(
                        float(cosine_sim(p_comment.body, c_comment.body)), 4)
                    commentCommentEdges.append(
                        (c_comment, p_comment, {"type": "SIMILARITY", "similarity": c_comment.similarity}))

        # add nodes for subgraph
        _nodes = []
        for cc, pc, *_ in commentCommentEdges:
            _nodes.append(cc)
            _nodes.append(pc)
        _nodes = list(set(_nodes)) #remove duplicates

        diGraph.add_edges_from(commentCommentEdges)
        graph.add_edges_from(authorCommentsEdges)
        graph.add_edges_from(commentCommentEdges)

        graph.add_edges_from(articleCommentEdges)
        graph.add_edges_from(sentimentCommentEdges)
        graph.add_nodes_from(nodes)

        # full graphs
        self._comment_graph = diGraph
        self._main_graph = graph

       # high level graphs
        self.group_graph_nodes = mp.clusterOnNumericPropertyNodes(2, _nodes, commentCommentEdges, num_internals=10)
        self.group_graph_edges = mp.clusterOnNumericProperty(2, commentCommentEdges, num_internals=10)
        
        return graph


if __name__ == "__main__":
    import matplotlib.pyplot as plt
    from models import CustomEncoder
    subreddit = "legaladvice"
    filename = "./raw/%s.json" % subreddit
    # username = input("Enter username:")
    # password = input("Enter password(Not hidden, so make sure no one is looking):")

    bot = GraphBot(subreddit)
    ids = list(bot.get_hot_submissions_id(2))
    graph = bot.getGraph(*ids)

    bot.dump(filename, ids)
    nx.write_graphml(graph, "./graphML/reddit_graph_%s.graphml" % subreddit)
    nx.write_graphml(bot.comment_graph,"./graphML/comment_graph_%s.graphml" % subreddit)
    nx.write_graphml(bot.group_graph_nodes, "./graphML/interval_graph_nodes.graphml")
    nx.write_graphml(bot.group_graph_edges, "./graphML/interval_graph_edges.graphml")

    # data = neonx.get_geoff(graph, "LINKS_TO", CustomEncoder())
    # nx.write_gexf(graph,"./graphML/neo.gexf")
    # neonx.write_to_neo("http://localhost:7687",graph,"LINKS_TO", encoder=CustomEncoder())
    # for g in bot.stream(subreddit):
    #     print(nx.clustering(g))
    # nx.draw(graph, with_labels=False, font_weight='bold')
    # plt.show()
    # bot.dump_submission_comments(submission_id, filename)

import csv
import nltk
import numpy as np
import networkx as nx
import random
nltk.download('punkt')
nltk.download('stopwords')
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.feature_extraction.text import CountVectorizer
from sklearn import preprocessing
from sklearn import svm

"""
    Possible changes
 - Lot of work to do on possible features from node_information.csv
 - Should try with nice random forests and XGBoost
 - Add other graph features

 Tiny details:
 -  Put binary = True in CountVectorizer constuction

"""#
with open("data/node_information.csv", "r") as f:
    file = csv.reader(f)
    node = list(file)

ID = [i[0] for i in node]
year=[i[1] for i in node]
title=[i[2] for i in node]
authors=[i[3] for i in node]
name_journal=[i[4] for i in node]
abstract=[i[5] for i in node]


"""
One_hot vectors on abstract (usefull for co_occurence computations in features construction function)
"""
one_hot = CountVectorizer(stop_words="english")
one_hot_matrix = one_hot.fit_transform(abstract)#.todense()
one_hot_matrix = one_hot_matrix.toarray()
print(one_hot_matrix.shape)
np.set_printoptions(threshold=np.nan)
print(sum(one_hot_matrix[1]))

"""
One_hot vectors on authors (usefull for co_occurence computations in features construction function)
"""
onehot_authors= CountVectorizer()
onehot_authors_matrix=onehot_authors.fit_transform(authors)
onehot_authors_matrix = onehot_authors_matrix.toarray()
print(onehot_authors_matrix.shape)
print(onehot_authors.get_feature_names())

"""
One_hot vectors on titles (usefull for co_occurence computations in features construction function)
"""
onehot_titles= CountVectorizer()
onehot_titles_matrix=onehot_titles.fit_transform(title)
onehot_titles_matrix = onehot_titles_matrix.toarray()
print(onehot_titles_matrix.shape)
print(onehot_titles.get_feature_names())

#####co_occurence computation (VERY EXPENSIVE)
# co_occurance_abstract=np.dot(cv_matrix,np.transpose(cv_matrix))
# co_occurance_abstract=np.dot(cv_matrix,cv_matrix.T)
"""
construction of the graph
"""
testtrain=0.9
with open("data/training_set.txt", "r") as f:
    file =csv.reader(f, delimiter='\t')
    set_file=list(file)
set= [values[0].split(" ") for values in set_file]
#creates the graph
G=nx.Graph()
#adds the list of papers' IDs
G.add_nodes_from(ID)
#adds the corresponding links between the paper (training set), links when link_test==1
##we only keep 90% of the set for testing perpose
for ID_source_train,ID_sink_train,link_train in set[:int(len(set)*testtrain)]:
    if link_train=="1":
        G.add_edge(ID_source_train,ID_sink_train)
#G.edges() to print all the edges

#check the number of edges
# G.number_of_edges()

#########
def features(paper1,paper2):
    """
        outputs the array of the features to input for paper1 and paper 2 comparison
    """
    idx_paper1,idx_paper2=ID.index(str(paper1)),ID.index(str(paper2))
    # print(abstract[ID.index(str(paper1))])
    # print(abstract[idx_paper1])

    #features from info of the nodes
    co_occurence_abstract=np.dot(one_hot_matrix[idx_paper1],one_hot_matrix[idx_paper2].T)
    same_authors=np.dot(onehot_authors_matrix[idx_paper1],onehot_authors_matrix[idx_paper2].T)
    co_occurence_title=np.dot(onehot_titles_matrix[idx_paper1],onehot_titles_matrix[idx_paper2].T)
    ## features over the graph
    jaccard = nx.jaccard_coefficient(G, [(str(paper1), str(paper2))])
    for u, v, p in jaccard:
        jaccard_coef= p
    adamic_adar=nx.adamic_adar_index(G, [(str(paper1), str(paper2))])
    for u, v, p in adamic_adar:
        adamic_adar_coef= p
    pref_attachement = nx.preferential_attachment(G, [(str(paper1), str(paper2))])
    for u, v, p in pref_attachement:
        pref_attachement_coef= p

    return [co_occurence_abstract,same_authors,co_occurence_title,jaccard_coef,adamic_adar_coef,pref_attachement_coef] #


train_features=[]
y_train=[]
print("Learning...")
step=0
for source,sink,link in set[:int(len(set)*testtrain)]: #
    step+=1
    if step%1000==0:    print("Step:",step,"/",int(len(set)*testtrain))
    train_features.append(features(source,sink))
    y_train.append(link)
train_features=np.array(train_features)
train_features = preprocessing.scale(train_features)
y_train=np.array(y_train)


# SVM as model
classifier = svm.LinearSVC()
# train the SVM
classifier.fit(train_features, y_train)


test_features=[]
y_test=[]
print("Testing...")
step=0
for source,sink,link in set[int(len(set)*testtrain):len(set)]: ##
    step+=1
    if step%1000==0:    print("Step:",step,"/",len(set)-int(len(set)*testtrain))
    test_features.append(features(source,sink))
    y_test.append(link)
test_features=np.array(test_features)
test_features = preprocessing.scale(test_features)
y_test=np.array(y_test)
test_features = preprocessing.scale(test_features)

# Prediction rate
pred = list(classifier.predict(test_features))
success_rate=sum(y_test==pred)/len(pred)

print("Success_rate:",success_rate)
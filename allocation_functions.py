
from agent_functions import Agent
from item_functions import Item, get_bundle_from_allocation_matrix, get_bundle_indexes_from_allocation_matrix
import networkx as nx
import matplotlib.pyplot as plt
import numpy as np

    

def initialize_allocation_matrix(items, agents):
    n=len(items)
    m=len(agents)+1 
    X=np.zeros([n,m],dtype=int)
    for i in range(n):
        X[i][0]=items[i].capacity
    return X

def initialize_exchange_graph(items):
    exchange_graph = nx.DiGraph()
    for i in range(len(items)):
        exchange_graph.add_node(i)
    t=i+1
    exchange_graph.add_node('t')
    for i in range(len(items)):
        exchange_graph.add_edge(i, 't')
    return exchange_graph

def initialize_players(agents):
    players=[]
    for i in range(len(agents)):
        players.append(i+1)
    return players

def get_max_items(items):
    max_items=0
    for i in range(len(items)):
        max_items+=items[i].capacity
    return max_items

def pick_agent(X,max_items,items, agents,players):
    max_capacity=max_items
    for player in players:
        agent=agents[player-1]
        bundle=get_bundle_from_allocation_matrix(X, items, player)
        current_utility=agent.valuation(bundle)
        if current_utility<max_capacity:
                max_capacity=current_utility
                agent_picked=player
    return agent_picked


def add_agent_to_exchange_graph(G,X,items,agents, agent_picked):
    G.add_node('s')
    bundle=get_bundle_from_allocation_matrix(X,items,agent_picked)
    for i in range(len(items)):
        g=items[i]
        if agents[agent_picked-1].marginal_contribution(bundle,g)==1:
            G.add_edge('s', i)
    return G

def find_shortest_path(G):
    try:
        p = nx.shortest_path(G, source='s', target='t') 
        return p
    except:
        return False

def find_agent(agents,items,X,current_item,last_item,current_item_index):
    #this could be made more efficiently, by going through only the owners and not every owner
    for i in range(len(agents)):
        bundle=get_bundle_from_allocation_matrix(X,items,i+1)
        if int(X[current_item_index,i+1]==1):
           if agents[i].exchange_contribution(bundle,current_item, last_item):        
                return i+1
    print('Agent not found') #this should never happen. If the item was in the path, then someone must be willing to exchange it

def get_owners_list(X,item_index):
    item_list=X[item_index]
    owners_list=np.nonzero(item_list)
    return owners_list[0]

def get_bundle_from_allocation_matrix(X, items, agent_index):
    bundle=[]
    items_list=X[:,agent_index]
    for i in range(len(items_list)):
        if int(items_list[i])==1:
            bundle.append(items[i])
    return bundle

def get_bundle_indexes_from_allocation_matrix(X, agent_index):
    bundle_indexes=[]
    items_list=X[:,agent_index]
    for i in range(len(items_list)):
        if int(items_list[i])==1:
            bundle_indexes.append(i)
    return bundle_indexes

def update_allocation(X,path_og,agents,items,agent_picked):
    path=path_og.copy()
    path=path[1:-1]
    last_item=path[-1]
    agents_involved=[agent_picked]
    X[last_item,0]-=1
    while len(path)>0:
        last_item=path.pop(len(path)-1)
        #print('last item: ', last_item)
        if len(path)>0:
            next_to_last_item=path[-1]
            #print('next to last item: ', next_to_last_item)
            current_agent=find_agent(agents,items,X,items[next_to_last_item],items[last_item],next_to_last_item)
            agents_involved.append(current_agent)
            #print('current agent: ', current_agent)
            X[last_item,current_agent]=1
            X[next_to_last_item,current_agent]=0
        else:
            X[last_item,agent_picked]=1
    return X, agents_involved


def update_exchange_graph(X,G,path_og,agents,items, agents_involved):
    path=path_og.copy()
    path=path[1:-1]
    last_item=path[-1]
    if X[last_item,0]==0:
        G.remove_edge(last_item,'t')
    for agent_index in agents_involved:
        bundle_indexes=get_bundle_indexes_from_allocation_matrix(X,agent_index)
        for item_idx in bundle_indexes:
            item_1=items[item_idx]
            owners=get_owners_list(X,item_idx)
            for owner in owners:
                if owner!=0:
                    agent=agents[owner-1]
                    desired_items_indexes=agent.get_desired_items_indexes(items)
                    for item_idx_2 in range(len(items)): #Change this to only search over desired items. 
                                                        #Doing item_idx_2 in desired_item_indexes is not working for some reason, DEBUGGGG!
                        if item_idx_2!=item_idx:
                            item_2=items[item_idx_2]
                            exchangeable=False               
                        
                            bundle_owner=get_bundle_from_allocation_matrix(X, items, owner)
                            willing_owner=agent.exchange_contribution(bundle_owner,item_1, item_2)
                            if willing_owner:
                                exchangeable=True
                            if exchangeable:
                                if not G.has_edge(item_idx, item_idx_2):
                                    G.add_edge(item_idx,item_idx_2)
                            else:
                                if G.has_edge(item_idx, item_idx_2):
                                    G.remove_edge(item_idx,item_idx_2)
    return G


def yankee_swap(agents,items, plot_exchange_graph):
    ## Initialize players, allocation, exchange_graph, and max utility
    players=initialize_players(agents)
    X=initialize_allocation_matrix(items, agents)
    print('Initial allocation:')
    print(X)
    G=initialize_exchange_graph(items)
    if plot_exchange_graph:
        nx.draw(G, with_labels = True)
        plt.show()
    max_items=get_max_items(items)
    ## Run Yankee Swap
    count=0
    while len(players)>0:
        count+=1
        print('STEP', count)
        agent_picked=pick_agent(X, max_items, items, agents,players)
        print('Agent picked:',agent_picked)
        G=add_agent_to_exchange_graph(G,X,items,agents, agent_picked)
        if plot_exchange_graph:
            nx.draw(G, with_labels = True)
            plt.show()

        path = find_shortest_path(G)
        print('path found:', path)
        G.remove_node('s')

        if path== False:
            players.remove(agent_picked)
        else:
            #Given the path found, update allocation and exchange graph
            X, agents_involved=update_allocation(X,path,agents,items,agent_picked)
            G=update_exchange_graph(X,G,path,agents,items, agents_involved)
            print('Current allocation:')
            print(X)
            print('involved agents:', agents_involved)
            if plot_exchange_graph:
                nx.draw(G, with_labels = True)
                plt.show()
    return X
            

    


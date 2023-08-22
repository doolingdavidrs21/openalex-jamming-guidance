import pandas as pd
import plotly.express as px
#import altair as alt
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network
import networkx as nx
import igraph as ig
from streamlit_plotly_events import plotly_events
import math
import plotly.io as pio
#pio.templates.default = "plotly"  
# https://towardsdatascience.com/how-to-deploy-interactive-pyvis-network-graphs-on-streamlit-6c401d4c99db
pio.templates.default = "plotly_dark"
# https://discuss.streamlit.io/t/streamlit-overrides-colours-of-plotly-chart/34943
st.set_page_config(layout='wide')

st.markdown("""
[China's plan for anti-satellite cyber weapon found in leaked CIA documents](https://techmonitor.ai/technology/cybersecurity/chinese-anti-satellite-cyber-weapon)

* radar jamming and deception (emission of radio signals to interfere with radar operation), 雷達壅塞與欺騙, Антирадар
* Electronic warfare (combat involving electronics and directed energy), радиоэлектронная борьба, 電子作戰
* Network-centric warfare, Сетецентрическая война, 網絡中心戰
* Missile guidance (variety of methods of guiding a missile), 导弹制导, Система самонаведения
""")

st.write("Topic modeling")

@st.cache_data()
def load_centroids_asat():
    #dg = pd.read_csv("penguins.csv", engine="pyarrow")
  #  df = pd.read_json(df.to_json())
    dg = pd.read_pickle('jammingcentroids2d.pkl.gz')
    #return dg
    return dg[dg.cluster != -1]

@st.cache_data()
def load_dftriple_asat():
    dg = pd.read_pickle('jammingdftriple2d.pkl.gz')
    return dg

@st.cache_data()
def load_dfinfo_asat():
    dg = pd.read_pickle('jammingdfinfo2d.pkl.gz')
    #return dg
    return dg[dg['cluster'] != -1]

#@st.cache_data()
#def load_dfgeo_asat():
#    dg = pd.read_pickle('asatgeo.pkl')
#    return dg





centroids = load_centroids_asat()
dftriple = load_dftriple_asat()
dfinfo = load_dfinfo_asat()
dfinfo['cluster_'] = dfinfo["cluster"].apply(str)
#dfgeo = load_dfgeo_asat()

kw_dict = dfinfo['keywords'].to_dict()

# add in the affiliations as nodes as well; that row, author, paper, affil. all three get links. ok.
def create_nx_graph(df: pd.DataFrame, cl:int) -> nx.Graph:
    """
    takes the dataframe df, and creates the undirected graph
    from the source and target columns for each row.
    """
    g = nx.Graph() # dc['paper_cluster'] == cl
    for index, row in df[df['paper_cluster'] == cl].iterrows():
        g.add_node(row['paper_id'], group='work', title=row['paper_title'])
        g.add_node(row['paper_author_id'], title=row['paper_author_display_name'],group='author')
        g.add_node(row['id'], group='affiliation',
                   title=row['display_name'] + '\n' + row['country_code'])
        if row['source']:
            g.add_node(row['source'], group=row['source_type'],
                      title=row['source'] + ' :\n ' + row['source_type'])
            g.add_edge(
                row['paper_id'],
                row['source'],
                weight = 10,
                title=row['paper_title'] + ' :\n ' + str(row['paper_publication_date']) +  \
                ' :\n' + row['source'] + ' :\n ' + \
                row['source_type']
            )
            g.add_edge(
                row['paper_author_id'],
                row['source'],
                title=row['paper_author_display_name'] + ':\n' + row['source']
            )
        if len(row['funder_list']) > 0:
            for f in row['funder_list']:
                g.add_node(f, group='funder',
                          title=str(f))
                g.add_edge(
                       row['paper_id'],
                       f,
                       title=row['paper_title'] + ':\n ' +  str(row['paper_publication_date']) + \
                       ' :\n' + str(f)
                   )
                g.add_edge(
                       f,
                       row['paper_author_id'],
                       title=row['paper_author_display_name'] + ' :\n ' + \
                       str(f)
                       
                   )
                g.add_edge(
                       f,
                       row['id'],
                       title=row['display_name'] + '\n' + row['country_code'] + ' :\n ' + \
                       str(f)                       
                   )  
                if row["source"]:
                    g.add_edge(
                        f,
                        row["source"],
                        title=row["source"] + ' :\n' + str(f)
                    )
        g.nodes[row['paper_id']]['title'] = (
            row['paper_title'] + ' :\n ' + str(row['paper_publication_date'] + ':\n' + 
            '\n'.join(kw_dict[row['paper_id']]))
        )
        g.nodes[row['paper_author_id']]['title'] = (
            row['paper_author_display_name']
        )
        g.add_edge(
            row['paper_id'],
            row['paper_author_id'],
            weight = 5,
        title=row['paper_title'] + ' :\n ' + row['paper_author_display_name'] + ' :\n ' + \
            row['paper_raw_affiliation_string']
        )
        g.add_edge(
            row['paper_id'],
            row['id'],
            weight = 15,
            title=row['paper_title'] + ' :\n ' + str(row['paper_publication_date']) + ':\n' + 
            row['display_name'] + ' :\n ' + row['country_code']
        )
        
    g_ig = ig.Graph.from_networkx(g) # assign 'x', and 'y' to g before returning
    layout = g_ig.layout_auto()
    coords = layout.coords
    allnodes = list(g.nodes())
    coords_dict = {allnodes[i]:(coords[i][0], coords[i][1]) for i in range(len(allnodes))}
    for i in g.nodes():
        g.nodes[i]['x'] = 500 * coords_dict[i][0] # the scale factor needed 
        g.nodes[i]['y'] = 500 * coords_dict[i][1]
    return g
                
                


#@st.cache_resource()
def create_pyvis_html(cl: int, filename: str = "pyvis_coauthorships_graph.html"):
    """
    wrapper function that calls create_nx_graph to finally 
    produce an interactive pyvis standalone html file
    """
    g_nx = create_nx_graph(dftriple, cl);
    h = Network(height="1000px",
          #  heading="Mitigations and Techniques Relationships",
                width="100%",
                cdn_resources="remote", # can grab the visjs library to make this local if needed
            # probably should
                bgcolor="#222222",
            neighborhood_highlight=True,
              # default_node_size=1,
                font_color="white",
                directed=False,
               # select_menu=True,
                filter_menu=True,
                notebook=False,
               )
    h.from_nx(g_nx, show_edge_weights=False)
    #h.barnes_hut()
    neighbor_map = h.get_adj_list()
   # for node in h.nodes:
   #     if node['group'] == 'author':
   #         a = list(neighbor_map[node["id"]]) # want to insert a "\n" into every third element of a
   #     if node['group'] == 'work':
   #         a = list(neighbor_map[node["id"]])
   #     i = 3
   #     while i < len(a):
   #         a.insert(i, "\n")
   #         i += 4
   #     node["title"] += "\n Neighbors: \n" + " | ".join(a)
   #     node["value"] = len(neighbor_map[node["id"]]) 
    h.set_options(
    """
const options = {
  "interaction": {
    "navigationButtons": false
  },
  "physics": {
    "enabled": false
  },
  "edges": {
    "color": {
        "inherit": true
    },
    "setReferenceSize": null,
    "setReference": {
        "angle": 0.7853981633974483
    },
    "smooth": {
        "forceDirection": "none"
    }
  }
  }
    """
    )
    #h.show_buttons(filter_=['physics'])
    try:
        path = './tmp'
        h.save_graph(f"{path}/{filename}")
        HtmlFile = open(f"{path}/{filename}","r",
                        encoding='utf-8')
    except:
        h.save_graph(f"{filename}")
        HtmlFile = open(f"{filename}", "r",
                        encoding="utf-8")
    return HtmlFile


#htmlfile = create_pyvis_html()


#st.map(dfgeo)

st.dataframe(centroids[['cluster','x','y','concepts','keywords']])

@st.cache_data()
def get_fig_asat():
    fig_centroids = px.scatter(centroids[centroids.cluster != -1],
                           x='x',y='y',
                    color_discrete_sequence=['pink'],
                          hover_data=['x','y',
                                      'wrapped_keywords',
                                      'wrapped_concepts','cluster'])
    fig_centroids.update_traces(marker=dict(size=12,
                              line=dict(width=.5,
                                        color='DarkSlateGrey')),
                  selector=dict(mode='markers'))
    fig_papers = px.scatter(dfinfo[dfinfo.cluster != -1],
                           x='x',y='y',
                    color='cluster_',
                        hover_data = ['title','cluster',
                                      'publication_date'])
                     #     hover_data=['title','x','y',
                     #                 'z','cluster','wrapped_author_list',
                     #                 'wrapped_affil_list',
                     #                 'wrapped_keywords'])
    fig_papers.update_traces(marker=dict(size=4,
                              line=dict(width=.5,
                                        color='DarkSlateGrey')),
                  selector=dict(mode='markers'))
    layout = go.Layout(
        autosize=True,
        width=1000,
        height=1000,

        #xaxis= go.layout.XAxis(linecolor = 'black',
         #                 linewidth = 1,
         #                 mirror = True),

        #yaxis= go.layout.YAxis(linecolor = 'black',
         #                 linewidth = 1,
         #                 mirror = True),

        margin=go.layout.Margin(
            l=10,
            r=10,
            b=10,
            t=10,
            pad = 4
            )
        )

    fig3 = go.Figure(data=fig_papers.data + fig_centroids.data)
    fig3.update_layout(height=700)

                   # layout=layout)  
    return fig3


#centroids = load_centroids()
#dftriple = load_dftriple()
#dfinfo = load_dfinfo()
#dfinfo['cluster_'] = dfinfo["cluster"].apply(str)
bigfig = get_fig_asat()

st.subheader("Papers and Topics")
st.write("Use the navigation tools in the mode bar to pan and zoom. Papers are automatically clustered into subtopics. Topics are the bigger pink dots with representative keywords and phrases available on hover. Clicking on a topic or paper then triggers a report of the most profilic countries, affiliations, and authors associated with that topic.")
selected_point = plotly_events(bigfig, click_event=True, override_height=700)
if len(selected_point) == 0:
    st.stop()
    
#st.write(selected_point)

selected_x_value = selected_point[0]["x"]
selected_y_value = selected_point[0]["y"]
#selected_species = selected_point[0]["species"]

try:
    df_selected = dfinfo[
        (dfinfo["x"] == selected_x_value)
        & (dfinfo["y"] == selected_y_value)
    ]

#def make_clickable(url, name):
#    return '<a href="{}" rel="noopener noreferrer" target="_blank">{}</a>'.format(url,name)

#df_selected['link'] = df_selected.apply(lambda x: make_clickable(x['id'], x['id']), axis=1)
    st.data_editor(
        df_selected[['x', 'y', 'id', 'title', 'doi', 'cluster', 'probability',
       'publication_date', 'keywords', 'top_concepts', 'affil_list',
       'author_list']],
        column_config={
            "doi": st.column_config.LinkColumn("doi"),
            "id": st.column_config.LinkColumn("id")
        },
        hide_index=True,
        )
    selected_cluster = df_selected['cluster'].iloc[0]
    st.write(selected_cluster)
except:
    df_selected_centroid = centroids[
        (centroids["x"] == selected_x_value)
        & (centroids["y"] == selected_y_value)
    ]
    selected_cluster = df_selected_centroid['cluster'].iloc[0]
    
    



#st.dataframe(df_selected)
#selected_cluster = df_selected['cluster'].iloc[0]
df_selected_centroid = centroids[
    (centroids['cluster'] == selected_cluster)
]
st.write(f"selected cluster: {selected_cluster}")
st.dataframe(df_selected_centroid[['concepts','keywords','x','y']])


def get_country_cluster_sort(dc:pd.DataFrame, cl:int):
    """
    restricts the dataframe dc to cluster value cl
    and returns the results grouped by id, ror sorted
    by the some of probablity descending
    """
    dg = dc[dc['paper_cluster'] == cl].copy()
   # print(cl)
    dv = dg.groupby(['country_code'])['paper_cluster_score'].sum().to_frame()
    dv.sort_values('paper_cluster_score', ascending=False, inplace=True)
    return dv, centroids[centroids.cluster == cl]['keywords'].iloc[0]


def get_affils_cluster_sort(dc:pd.DataFrame, cl:int):
    """
    restricts the dataframe dc to cluster value cl
    and returns the results grouped by id, ror sorted
    by the some of probablity descending
    """
    dg = dc[dc['paper_cluster'] == cl].copy()
    print(cl)
    dv = dg.groupby(['id','display_name','country_code',
                     'type'])['paper_cluster_score'].sum().to_frame()
    dv.sort_values('paper_cluster_score', ascending=False, inplace=True)
    dv.reset_index(inplace=True)
    kw = centroids[centroids.cluster == cl]['keywords'].iloc[0]
    return dv, kw


def get_author_cluster_sort(dc:pd.DataFrame, cl:int):
    """
    restricts the dataframe dc to cluster value cl
    and returns the results grouped by id, ror sorted
    by the some of probablity descending
    """
    dg = dc[dc['paper_cluster'] == cl].copy()
   # print(cl)
    dv = dg.groupby(['paper_author_id','paper_author_display_name',
                    'display_name',
                     'country_code'])['paper_cluster_score'].sum().to_frame()
    dv.sort_values('paper_cluster_score', ascending=False, inplace=True)
    dv.reset_index(inplace=True)
    return dv, centroids[centroids.cluster == cl]['keywords'].iloc[0]


def get_journals_cluster_sort(dc:pd.DataFrame, cl:int):
    """
    restricts the dataframe dc to cluster value cl
    and returns the results grouped by source (where
    source_type == 'journal') sorted
    by the some of probablity descending
    """
    dg = dc[dc['paper_cluster'] == cl].copy()
    print(cl)
    dv = dg[dg['source_type'] == 'journal'].groupby(['source'])['paper_cluster_score'].sum().to_frame()
    dv.sort_values('paper_cluster_score', ascending=False, inplace=True)
    dv['journal'] = dv.index
    kw = centroids[centroids.cluster == cl]['keywords'].iloc[0]
    return dv, kw


def get_conferences_cluster_sort(dc:pd.DataFrame, cl:int):
    """
    restricts the dataframe dc to cluster value cl
    and returns the results grouped by source (where
    source_type == 'journal') sorted
    by the some of probablity descending
    """
    dg = dc[dc['paper_cluster'] == cl].copy()
    print(cl)
    dv = dg[dg['source_type'] == 'conference'].groupby(['source'])['paper_cluster_score'].sum().to_frame()
    dv.sort_values('paper_cluster_score', ascending=False, inplace=True)
    dv['conference'] = dv.index
    kw = centroids[centroids.cluster == cl]['keywords'].iloc[0]
    return dv, kw


def get_country_collaborations_sort(dc:pd.DataFrame, cl:int):
    """
    resticts the dataframe dc to cluster value cl
    and returns the results of paper_id s where there is 
    more than one country_code
    """
    dg = dc[dc['paper_cluster'] == cl].copy()
    dv = dg.groupby('paper_id')['country_code'].apply(lambda x: len(set(x.values))).to_frame()
    dc = dg.groupby('paper_id')['country_code'].apply(lambda x: list(set(x.values))).to_frame()
    dc.columns = ['collab_countries']
    dv.columns = ['country_count']
    dv['collab_countries'] = dc['collab_countries']
    dv.sort_values('country_count',ascending=False, inplace=True)
    di = dfinfo.loc[dv.index].copy()
    di['country_count'] = dv['country_count']
    di['collab_countries'] = dv['collab_countries']
    return di[di['country_count'] > 1]




tab1, tab2, tab3, tab4 , tab5, tab6, tab7= st.tabs(["Countries", "Affiliations", "Authors",
                                        "Journals","Conferences",
 "Coauthorship Graph", "Country-Country Collaborations"])

dvauthor, kwwuathor = get_author_cluster_sort(dftriple, selected_cluster)
#st.dataframe(dvauthor)

dfcollab = get_country_collaborations_sort(dftriple, selected_cluster)

dvaffils, kwwaffils = get_affils_cluster_sort(dftriple, selected_cluster)
        
dc, kw = get_country_cluster_sort(dftriple, selected_cluster)


dvjournals, kwjournals = get_journals_cluster_sort(dftriple, selected_cluster)

dvconferences, kwconferences = get_conferences_cluster_sort(dftriple, selected_cluster)

htmlfile = create_pyvis_html(selected_cluster)

with tab1:
    st.dataframe(dc)
with tab2:
    st.markdown("highlight and click a value in the **id** column to be given more information")
    st.data_editor(
        dvaffils,
        column_config={
            "id": st.column_config.LinkColumn("id"),
        },
        hide_index=True,
    )
    #st.dataframe(dvaffils)
with tab3:
    st.write("highlight and click a value in the **paper_author_id** to be given more information")
    st.data_editor(
        dvauthor,
        column_config={
            "paper_author_id": st.column_config.LinkColumn("paper_author_id")
        },
        hide_index=True,
    )
    
with tab4:
    st.write("Journals most representative of this cluseter")
    st.dataframe(
        dvjournals[['journal','paper_cluster_score']],
        hide_index=True
    )

    
with tab5:
    st.write("Conferences most representative of this cluseter")
    st.dataframe(
        dvconferences[['conference','paper_cluster_score']],
        hide_index=True
    )
    
# https://ieeexplore.ieee.org/stamp/stamp.jsp?arnumber=9266366

with tab6:
    st.write("Coauthorship Graph (Papers and Authors)")
    components.html(htmlfile.read(), height=700)
    
with tab7:
    st.write("Country-Country Collaborations")
    st.data_editor(
        dfcollab[['x', 'y', 'id','collab_countries', 'title', 'doi', 'cluster', 'probability',
       'publication_date', 'keywords', 'top_concepts', 'affil_list',
       'author_list','funder_list']],
        column_config={
            "doi": st.column_config.LinkColumn("doi"),
        },
        hide_index=True,
    )
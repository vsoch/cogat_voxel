from flask import Flask, render_template
import random
import pandas
import pickle

# SERVER CONFIGURATION ##############################################
class CogatServer(Flask):

    def __init__(self, *args, **kwargs):
            super(CogatServer, self).__init__(*args, **kwargs)

            # load data on start of application
            self.df = pandas.read_pickle("data/regression_params.pkl")
            self.images = pandas.read_csv("data/contrast_defined_images_filtered.tsv",sep="\t",index_col="image_id")
            self.Y = pandas.read_csv("data/images_contrasts_df.tsv",sep="\t",index_col=0)
            self.lookup = pandas.read_csv("data/cogatlas_concepts.tsv",sep="\t",index_col=0)

            # D3 specific variables
            self.width = 1500
            self.height = 370
            self.padding = 12
            self.radius = 5
            self.maxRadius = 12
          
            # Image data
            self.X = pickle.load(open("data/images_df.pkl","rb"))
            # value will be radius, we don't want negative values
            self.X = self.X + self.X.min().abs()

            # Pairwise spatial similarity
            self.spatial = pandas.read_csv("data/contrast_defined_images_pearsonpd_similarity.tsv",sep="\t",index_col=0)

app = CogatServer(__name__)

# Global variables for app

### Helper Functions
def make_node(concept,tagged_image,v):
  image = app.images.loc[tagged_image]
  return {
    "radius": app.radius,
    "concept": concept,
    "concept_name":app.lookup.name[app.lookup.id==concept].tolist()[0],
    "contrast": image.cognitive_contrast_cogatlas,
    "task": image.cognitive_paradigm_cogatlas,
    "collection": image.collection_id,
    "thumbnail": image.thumbnail,
    "value": app.X.loc[tagged_image,v],
    "uid":tagged_image
   }

def get_lookup():
    lookup = dict()
    for row in app.lookup.iterrows():
        lookup[row[1].id] = row[1]["name"] #cannot be .name
    return lookup

def random_colors(concepts):
    '''Generate N random colors'''
    colors = {}
    for x in range(len(concepts)):
        concept = concepts[x]
        r = lambda: random.randint(0,255)
        colors[concept] = '#%02X%02X%02X' % (r(),r(),r())
    return colors


@app.route("/<v>")
def voxel(v):

    v = int(v)

    # Prepare variables
    regparams = app.df.loc[v]

    # We are only interested in nonzero concepts
    regparams = regparams[regparams!=0]
    concepts = regparams.index.tolist()
    colors = random_colors(concepts)
    regparams = regparams.to_json()

    nodes = []
    unique_images = []  
    # prepare list of images for each concept
    for concept in concepts:
        tagged_images = app.Y.index[app.Y[concept]==1].tolist() 
        for tagged_image in tagged_images:
            nodes.append(make_node(concept,tagged_image,v))
            if tagged_image not in unique_images:
                unique_images.append(tagged_image)

    # Generate a lookup by concept name
    lookup = get_lookup()

    # We only need spatial similarity for images relevant to concept
    spatial = app.spatial.loc[unique_images,[str(x) for x in unique_images]]
    spatial = (spatial-1).abs().to_json() # needs to be a positive distance between 0 and 1

    return render_template("index.html",regparams=regparams,
                                        M=len(concepts),
                                        N=len(nodes),
                                        min=app.df.loc[v].min(),
                                        max=app.df.loc[v].max(),
                                        width=app.width,
                                        height=app.height,
                                        padding=app.padding,
                                        radius=app.radius,
                                        maxRadius=app.maxRadius,
                                        nodes=nodes,
                                        spatial=spatial,
                                        lookup=lookup,
                                        colors=colors,
                                        voxel=v)


@app.route("/")
def index():

    return voxel(0)


if __name__ == "__main__":
    app.debug = True
    app.run()


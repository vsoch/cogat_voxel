from pybraincompare.report.colors import random_colors
from flask import Flask, render_template
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
            self.width = 1500
            self.height = 500
            self.padding = 6
            self.radius = 5
            self.maxRadius = 12


app = CogatServer(__name__)

# Global variables for app

### Helper Functions
def make_node(concept,tagged_image):
  image = app.images.loc[tagged_image]
  return {
    "radius": app.radius,
    "concept": concept,
    "task": image.cognitive_paradigm_cogatlas_id,
    "collection": image.collection_id,
    "thumbnail": image.thumbnail
   }



@app.route("/")
def showcase():

    # Prepare variables
    voxel=0 # This will eventually come from browser url
    regparams = app.df.loc[voxel]
    # We are only interested in nonzero concepts
    regparams = regparams[regparams!=0]
    concepts = regparams.index.tolist()
    regparams = regparams.to_json()

    nodes = []
    # prepare list of images for each concept
    for concept in concepts:
        tagged_images = app.Y.index[app.Y[concept]==1].tolist() 
        for tagged_image in tagged_images:
            nodes.append(make_node(concept,tagged_image))

    return render_template("index.html",concepts=concepts,
                                        regparams=regparams,
                                        M=len(concepts),
                                        N=app.images.shape[voxel],
                                        min=app.df.loc[voxel].min(),
                                        max=app.df.loc[voxel].max(),
                                        images=app.images.to_json(),
                                        width=app.width,
                                        height=app.height,
                                        padding=app.padding,
                                        radius=app.radius,
                                        maxRadius=app.maxRadius,
                                        nodes=nodes)

@app.route("/neurovault")
def show_tagged_images():

    # Retrieve neurovault images, sort
    url = "contrasts_nv.json"
    images = pandas.io.json.read_json(url)
    images = images.sort(columns="cognitive_paradigm_cogatlas")

    # Generate a color for each task
    tasks = images["cognitive_paradigm_cogatlas"].unique()
    num_contrasts = len(tasks)
    colors = random_colors(num_contrasts)
    color_lookup = dict()
    for c in range(0,len(colors)):
        color_lookup[tasks[c]] = colors[c]
    colorvector = [color_lookup[x] for x in images.cognitive_paradigm_cogatlas.tolist()]
    images["color"] = colorvector

    # Prepare variables for context
    names = images["name"].tolist()
    contrasts = images["contrast_definition"].tolist()
    tasks = images["cognitive_paradigm_cogatlas"].tolist()
    urls = images["url"].tolist()
    colors = images["color"].tolist()
    thumbnails = images["thumbnail"].tolist()
 
    # render images with contrasts tagged
    return render_template("neurovault.html",context=zip(names,contrasts,tasks,urls,colors,thumbnails))

if __name__ == "__main__":
    app.debug = True
    app.run()


import json
class Posts:
    template="""<div class="container mt-5">
    <div class="card">
    <div class="card-header">
      <h4><TITLE></h4>
    </div>
    <div class="card-body">
      <div class="row">
        <!-- Text Column -->
        <div class="col-md-6">
          <p class="lead">
          <TEXT>
          </p>
        </div>
        <!-- Image Column -->
        <div class="col-md-6">
          <img src="<IMGLOC>" alt="<IMG_ALT_TEXT>" class="img-fluid rounded w-100">
        </div>
      </div>
    </div>
    </div>
    </div>"""
    header="""<!DOCTYPE html>
    <html lang="en">
    <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Parsa Ghadermazi - Microbiome Researcher</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH" crossorigin="anonymous">
    </head>
    <body>
    <nav class="navbar navbar-expand-lg bg-body-tertiary">
        <div class="container-fluid">
        <a class="navbar-brand" href="index.html">Parsa Ghadermazi</a>
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNavAltMarkup" aria-controls="navbarNavAltMarkup" aria-expanded="false" aria-label="Toggle navigation">
            <span class="navbar-toggler-icon"></span>
        </button>
        <div class="collapse navbar-collapse" id="navbarNavAltMarkup">
            <div class="navbar-nav">
            <a class="nav-link active" aria-current="page" href="posts.html">Posts</a>
            <a class="nav-link" href="publications.html">Publications</a>
            <a class="nav-link" href="contact.html">Contact Me</a>
            </div>
        </div>
        </div>
        </nav>
    """
    def make_html_from_json(self, json_input,outpath):
        with open(json_input, 'r') as f:
            data = json.load(f)
        t=self.template
        html_text=self.header
        for post in data:
            html_text+=t.replace("<TITLE>",post["title"]).replace("<TEXT>",post["body"]).replace("<IMGLOC>",post["image"]).replace("<IMG_ALT_TEXT>",post["alt_text"])
    
        with open(outpath, 'w') as f:
            f.write(html_text)
        
    def publish_posts(self, json_input:str="data/posts.json", outpath:str="posts.html"):
        self.make_html_from_json(json_input, outpath)
        print("Posts published successfully")
    
    

class Publication:
    pass

if __name__=="__main__":
    p=Posts()
    p.publish_posts()
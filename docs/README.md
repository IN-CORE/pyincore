## pyIncore documentation

**pyIncore** documentation which is built using Python [Sphinx](http://www.sphinx-doc.org/en/master/) package.

### Installation

Clone the code from pyincore repository [git](https://opensource.ncsa.illinois.edu/bitbucket/scm/incore1/pyincore.git) 
repository.

### Building and running Sphinx in Docker container

Install [Docker Desktop](https://www.docker.com/) for your OS and change directory to your local branch `pyincore/docs` folder (one with Dockerfile).

1. Build container
    ```
    docker build -t pyincore_docs .
    ```
    The container's name is **pyincore_docs** in this example.
    
2. Run docker
    ```
    docker run --rm -p 80:80 --name doctest pyincore_docs:latest
    ```
    Optional flag, `-name` sets container's name to **doctest** under which it appears in Docker Desktop.
   
3. Run html pages in your local browser (you might see the nginx main page first)
    ```
    http://localhost/doc/pyincore/
    ``` 

 

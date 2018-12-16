Application for generating SBGN diagram of SBML reactions and BCSL rules.

After installation, Swagger generate a documentation of API endpoints,
with examples.


**Requirements**: potrace, python 3.6.x, virtualenv

For installation need to have also pip and git.

Go to source folder and create new [virtualenv](https://packaging.python.org/guides/installing-using-pip-and-virtualenv/).
```
$ virtualenv -p python3 env
```
Active .env and install requirements. 
```
$ pip install -r requirements.txt
```
Need to install submodule BCSLRuleParser. Pull by:
```
$ git submodule init && git submodule update
```
Tutorial available [here](https://github.com/sybila/BCSLruleParser).
(In tutorial is missing one step: In directory is needed to create also `build` folder.)

Run app by ```python app.py```

If running with default host and port, check Swagger documentation:
http://localhost:5000/api/ui/#/

There is also possible to try requests.
(Swagger will display only PNG, SVG is not supported. Its mostly for documantation)
To get SVG, call as normal HTTP request.

(Application was tested on unix-based systems. 
Windows will maybe required some other dependencies or changes in codebase.)
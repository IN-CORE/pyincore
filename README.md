# pyincore

*pyincore* is a python module that can be used to write workflow tools. 

To install the package, download the source code and then from the terminal run:

`python setup.py install`

# pyincore tests
In order to run Tests, you need to create a file called, ".incorepw" under tests folder.
The file needs to lines: user name in 1st line, password in 2nd line


# Notes

There is a known issue running analyses on multiple threads in some versions of python 3.6.x running on MacOS High Sierra 10.13.x
If you see such errors on your environment, set the below environment variable in your .bash_profile as a workaround.

`export OBJC_DISABLE_INITIALIZE_FORK_SAFETY=YES` 
 
Issue details can be found [here](http://sealiesoftware.com/blog/archive/2017/6/5/Objective-C_and_fork_in_macOS_1013.html)

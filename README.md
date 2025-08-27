# autocanvas
Automate simple Canvas tasks related to course enrollments.

Dependencies:
* Python 3.6+.
* CanvasAPI, installation instructions: https://canvasapi.readthedocs.io/en/stable/getting-started.html#installing-canvasapi.

Relevant API documentation:
* https://canvas.instructure.com/doc/api/enrollments.html
* https://canvasapi.readthedocs.io/en/stable/course-ref.html
* https://canvasapi.readthedocs.io/en/stable/enrollment-ref.html

To create a Canvas API key:
* Go to Canvas --> Profile --> Settings.
* Click on 'Approved integrations' --> 'New access token'.

Usage (simple mode):

```shell
$ cp params_default.py params.py # and edit params.py
$ ./autocanvas.py
```

Example workflow to delete unenrolled students from a course:
* Create a Canvas API key as described above.
* Create a `params.py` file from `params_default.py` file.
* Edit `params.py` as follows:
  * `API_KEY`: Paste your newly created API key (access token).
  * `API_URL`: Edit the base URL if necessary.
  * `course`: Enter your course ID.
  * `user_file`: Enter the name of the file with all the *enrolled* students.
* Run `./autocanvas.py` to verify the list of to-be-deleted unenrolled ones.
* Edit `params.py` again as follows:
  * `action`: Enter `delete` (Warning: this action cannot be undone).
* Run `./autocanvas.py` again to actually delete unenrolled students. 
  
Usage (batch mode, note this requires admin rights):

```shell
$ cp params_default.py params.py # and edit params.py
$ ./autocanvas-batch.py
```

Example workflow to refresh all the students of a course:
* Create a Canvas API key as described above.
* Create a `params.py` file from `params_default.py` file.
* Edit `params.py` as follows:
  * `API_KEY`: Paste your newly created API key (access token).
  * `API_URL`: Edit the base URL if necessary.
  * `user_file`: Enter the name of the file with all the <course,student-number> pairs.
* Run `./autocanvas-batch.py` to verify the list of to-be-deleted/added students.
* Edit `params.py` again as follows:
  * `action`: Enter `new-active` (Warning: this action cannot be undone).
* Run `./autocanvas-batch.py` again to actually refresh the course.

## GUI mode

For a simple graphical interface run:

```shell
$ python canvas_gui.py
```

Enter your Canvas API URL and key, load the available courses and then
add or remove students from the selected course.  The application caches
course and enrollment information locally so it remains responsive even
when working with large numbers of courses or students.

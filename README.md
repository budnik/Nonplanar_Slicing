<a name="readme-top"></a>

# Nonplanar Gcode Transformation


## About The Project


This project is the main part of the project work from Samuel Maissen and Severin Zürcher at ZHAW School of Engineering, Switzerland

Our main goal was to implement two different algorithm for producing non-planar GCode from planar slicing Software.
* Final GCode is created through transforming a .stl part to get a flat surface, slicing this transformed .stl and scale the planar Gcode in relation to the surface from the original part. With this algorithm, you get a GCode with different scaled layer heights throughout the same layer.
* Final GCode is created through turnig the part upside down, slice the part and pull the GCode to the buildplate, so that the original shape is recreated.

Currently the ironing process works but still not perfect

<p align="right">(<a href="#readme-top">back to top</a>)</p>



### Built With

The implementation is completly based on Python 3.11, build with Visual Studio Code and sliced with Prusaslicer 2.7.0

<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f8/Python_logo_and_wordmark.svg/2560px-Python_logo_and_wordmark.svg.png" width="300" height="100">   <img src="https://code.visualstudio.com/assets/images/code-stable.png" width="90" height="90">    <img src="https://help.prusa3d.com/wp-content/uploads/PSlogo-1.jpg" width="110" height="110">
<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Getting Started

Make sure to have your favourite IDE with Python 3.11 and Prusaslicer 2.7.0 on your machine installed (preferably with Anaconda)


### Installation

To set up the project and install dependencies:

1.  **Clone the repository (if you haven't already):**
    ```sh
    git clone <your-repository-url>
    cd <your-repository-name>
    ```

2.  **Create and activate a Python 3 virtual environment:**

    * On macOS and Linux:
        ```sh
        python3 -m venv venv
        source venv/bin/activate
        ```
    * On Windows:
        ```sh
        python -m venv venv
        .\venv\Scripts\activate
        ```
    You should see `(venv)` at the beginning of your command prompt, indicating the virtual environment is active.

3.  **Install the required Python packages:**
    Ensure you have a `requirements.txt` file in the root of your project directory. Then, run the following command to install all necessary dependencies:
    ```sh
    pip install -r requirements.txt
    ```

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Usage

Run main.py (main_Mac.py on Mac computers) to open the GUI.

Select your .stl file and the .ini config file (directly exported from Prusaslicer -> Ctrl + E)

Select the Path for your Prusaslicer.exe installation -> Standard path is predefined

Select the method you want to use:
* Method 1 adds a option to create an offset from the outline for rounded edges
* Method 2 adds the options to define the number of planar baselayers and the transformation method

Press "Calculate GCode" and wait for completion. For preview press "Open Nonplanar GCode"

Now you have your Non-planar GCode for printing.

### Tipps
* Check the maximal possible printing angle to avoid crashing your Z-Probe of Fan with the print
* It works stable with STL parts that have a flat baselayer and vertical sides.
* If the part has edges in the middle of the part, try reexporting the part from CAD or setting the origin of the STL at the Center of the part
* If method 2 takes too long, decrease the resolution of the z-Mesh
* If method 2 produces errors at the edges use transformation method "mirror" for transformation or increase resolution
* For method 2 transformation method "mirror" is more robust, than "interpolate"
* If you use the scripts on a Mac computer make sure to rename the Prusa slicer in the Application folder to: "Original_Prusa_Drivers"

<p align="right">(<a href="#readme-top">back to top</a>)</p>



## Contact

Samuel Maissen  - samuel.j.maissen@gmail.com

Severin Zürcher - zuercher.severin@bluewin.ch

Michael Wüthrich - wuem@zhaw.ch

Project Link: [https://github.com/RotBotSlicer/Nonplanar_Slicing](https://github.com/RotBotSlicer/Nonplanar_Slicing/tree/main)

<p align="right">(<a href="#readme-top">back to top</a>)</p>
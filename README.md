# HalfFrameUtils

A collection of tools that help with post prcessing photos with an emphasis on half frame photograohy. Features so far include:

- Splitting diptychs (2 half frame exposures on a single frame) into individual images.
- Converting images to black and white.

Limitations:
 - Currently only supports jpgs.

## Installation and Usage

### Installation

- Clone this repository

`https://github.com/jlips24/HalfFrameUtils.git`

- Navigate to the root folder of the project in your terminal
- (Optional but recomended) Create a virtual environment

`python -m venv venv`

- (If using virtual environment) Activate the virtual environment

`source venv/bin/activate`

- Install requirements

`pip install -r requirements.txt`

### Desktop GUI

Launch the graphical interface:

`python HalfFrameUtilsGUI.py`

Choose an input folder and output folder, select one or both processing operations, and click **Process images**.

Prebuilt desktop applications are produced through GitHub Actions. Maintainers can find the build, testing, and version-tag release process in [the release guide](docs/RELEASING.md).


### Usage
The general usage for this tool is as follows:

`python HalfFrameUtils.py -hf -i ./input_folder -o ./output_folder`


#### Flags and arguements
| Argument     | Shorthand | Type   | Description                                 | Required |
|--------------|-----------|--------|---------------------------------------------|----------|
| --halfframe  | -hf       | None   | Splits half frame exposures into two images | No       |
| --blackwhite | -bw       | None   | Converts images to grayscale                | No       |
| --input      | -i        | String | Input folder path                           | Yes      |
| --output     | -o        | String | Output folder path                          | Yes      |

## Examples

###### All borders shown are for presenting the results and do not actually show up in the resulting image

### Splitting Half Frame

Original Image:

<kbd>
    <img src="./docs/imgs/HFBefore.jpg" alt="Input Image" height="300"/>
</kbd>


Command: `python HalfFrameUtils.py -i ./input -o ./output -hf`

Output Images:

<kbd>
    <img src="./docs/imgs/HFAfter-1.jpg" alt="Output Image 1" height="300"/>
</kbd>
<kbd>
    <img src="./docs/imgs/HFAfter-2.jpg" alt="Output Image 2" height="300"/>
</kbd>

### Converting to black and white

Original Image:

<kbd>
    <img src="./docs/imgs/HFAfter-1.jpg" alt="Input Image" height="300"/>
</kbd>

Command: `python HalfFrameUtils.py -i ./input -o ./output -bw`

Output Image:

<kbd>
    <img src="./docs/imgs/BWAfter.jpg" alt="Output Image Image" height="300"/>
</kbd>

# VoronoiCity2

Inspired by old Tokyo office districts like Marunouchi,
I created an office district using an approach different from [VoronoiCity](https://github.com/taKana671/VoronoiCity). Using libraries like scipy and shapely, I generated bounded Voronoi regions, then scaled down each region to form roads. Each region was further Voronoi-partitioned, and random prisms were generated from the partitioned region vertices to form buildings.
The layout of buildings and parks, as well as building heights, are dynamically calculated and therefore change each time the script is run.

<img width="790" height="592" alt="Image" src="https://github.com/user-attachments/assets/8a5669db-c066-440d-943b-7c6f4fa3494b" />

# Requirements
* Panda3D 1.10.16
* numpy 2.2.6
* shapely 2.1.2
* scipy 1.16.2
  
# Environment
* Python 3.13
* Windows11

# Usage

#### Clone this repository with submodule.
```
git clone --recursive https://github.com/taKana671/VoronoiCity2.git
```

#### Execute the following command
```
python voronoi_city_2.py
```

#### Key control

<table>
    <tr>
      <th>key</th>
      <th>description</th>
    </tr>
    <tr>
      <th>Esc</th>
      <th align="left">Close the screen.</th>
    </tr>
    <tr>
      <th>t</th>
      <th align="left">Toggles physical object display on and off.</th>
    </tr>
    <tr>
      <th>w</th>
      <th align="left">Toggles wireframe display on and off.</th>
    </tr>
    <tr>
      <th>v</th>
      <th align="left">Switch between sky view mode and moving view mode.</th>
    </tr>
</table>

In `skyview mode`, you can view the city from above and rotate the entire city by dragging the mouse. 
`moving view mode` allows you to move around the city by keystrokes below.
<table>
    <tr>
      <th>key</th>
      <th>description</th>
    </tr>
    <tr align="left">
      <th>up arrow</th>
      <th>Move forward.</th>
    </tr>
    <tr align="left">
      <th>left arrow</th>
      <th>Turn left.</th>
    </tr>
    <tr align="left">
      <th>right arrow</th>
      <th>Turn right.</th>
    </tr>
    <tr align="left">
      <th>down arrow</th>
      <th>Move backward.</th>
    </tr>
    <tr align="left">
      <th>u</th>
      <th>Go up.</th>
    </tr>
    <tr align="left">
      <th>d</th>
      <th>Go down.</th>
    </tr>
</table>

https://github.com/user-attachments/assets/1d2c428f-3673-44c5-a834-26679568494b

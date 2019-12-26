import cjlano_svg as svg
from os import path

from svg2stl.model import Polygon, Point, Color
import svg2stl.scad as s
from svg2stl.util import filter_repetition

import tinycss2 as css
import tinycss2.ast

px = 25.4 / 96

datapath = path.join("..", "testdata")
outputpath = path.join(datapath, "output")
svg_file_name = path.join(datapath, "test2.svg")
scad_file_name = path.join(outputpath, "output.scad")

svg_picture = svg.parse(svg_file_name)
svg_paths = svg_picture.flatten()

precision=1
thickness=1

def extract_color(svg_object):
    style = svg_object.style
    declarations = css.parse_declaration_list(style)
    for declaration in declarations:
        if isinstance(declaration, css.ast.Declaration):
            if declaration.lower_name == "fill":
                value = declaration.value[0]
                if isinstance(value, css.ast.HashToken):
                    return Color.from_html(value.value)
    return None

# Create the polygons
polygons=list()
for index, path in enumerate(svg_paths):
    polygon = Polygon(path.id)
    polygon.color = extract_color(path)
    for subpath in path.segments(precision):
        polygon.add_subpolygon((Point(p.x, -p.y) for p in filter_repetition(subpath)))
    polygons.append(polygon)




with open(scad_file_name, "w") as file:
    scad_file = s.File(file)

    for polygon in polygons:
        points_name = f"{polygon.name}_points"
        scad_file.output(s.Assignment(points_name, polygon.points))

        for index, path in enumerate(polygon.paths):
            path_name = f"{polygon.name}_path_{index}"
            scad_file.output(s.Assignment(path_name, path))

    print(file=file)
    for index, polygon in enumerate(polygons):
        points_name = f"{polygon.name}_points"
        path_names = (f"{polygon.name}_path_{index}" for index, path in enumerate(polygon.paths))
        poly = s.Polygon(polygon, points_name, path_names)
        module = s.Module(polygon.name, [poly])
        scad_file.output(module)

    print(file=file)
    for index in range(len(polygons)):
        difference = s.Difference((s.Instance(p.name) for p in polygons[index:]))
        name = f"{polygons[index].name}_only"
        module = s.Module(name, [difference])
        scad_file.output(module)

    print(file=file)
    for index, polygon in enumerate(polygons):
        #color = Color.from_hsv(index / len(polygons), 1, 1)
        color = polygon.color
        instance = s.Instance(f"{polygon.name}_only")
        extrude = s.Extrude(thickness, instance)
        translate = s.Translate((0, 0, 0 * index * thickness), extrude)
        o = s.Color(color, translate)
        scad_file.output(o)

# -*- coding: utf-8 -*-
from operator import itemgetter, add

from pygal.util import node, flatten, float_range
from pygal.graph import Graph


class Line(Graph):
    """Line Graph"""

    """Show a small circle on the graph where the line goes from one point to
    the next"""
    show_data_points = True
    show_data_values = True
    """Accumulates each data set. (i.e. Each point increased by sum of all
    previous series at same point)."""
    stacked = False
    "Fill in the area under the plot"
    area_fill = False

    scale_divisions = None

    # override some defaults
    top_align = top_font = right_align = right_font = True

    stylesheet_names = Graph.stylesheet_names + ['plot.css']

    def max_value(self):
        data = map(itemgetter('data'), self.data)
        if self.stacked:
            data = self.get_cumulative_data()
        return max(flatten(data))

    def min_value(self):
        if self.min_scale_value:
            return self.min_scale_value
        data = map(itemgetter('data'), self.data)
        if self.stacked:
            data = self.get_cumulative_data()
        return min(flatten(data))

    def get_cumulative_data(self):
        """Get the data as it will be charted.  The first set will be
        the actual first data set.  The second will be the sum of the
        first and the second, etc."""
        sets = map(itemgetter('data'), self.data)
        if not sets:
            return
        sum = sets.pop(0)
        yield sum
        while sets:
            sum = map(add, sets.pop(0))
            yield sum

    def get_x_labels(self):
        return self.fields

    def calculate_left_margin(self):
        super(self.__class__, self).calculate_left_margin()
        label_left = len(self.fields[0]) / 2 * self.font_size * 0.6
        self.border_left = max(label_left, self.border_left)

    # TODO: cache this
    def get_y_label_values(self):
        max_value = self.max_value()
        min_value = self.min_value()
        range = max_value - min_value

        scale_division = self.scale_divisions or (.105 * range)

        if self.scale_integers:
            scale_division = round(scale_division)

        scale_division = scale_division or 1  # prevent / 0

        if max_value % scale_division == 0:
            max_value += scale_division
        labels = tuple(float_range(min_value, max_value, scale_division))
        if self.scale_integers:
            labels = map(int, labels)
        return labels

    def get_y_labels(self):
        return map(str, self.get_y_label_values())

    def calc_coords(self, field, value, width=None, height=None):
        if width is None:
            width = self.field_width
        if height is None:
            height = self.field_height
        coords = dict(
            x=width * field,
            y=self.graph_height - value * height,
            )
        return coords

    def draw_data(self):
        if len(self.data) == 0:
            return

        min_value = self.min_value()

        field_height = self.graph_height - self.font_size * 2 * self.top_font
        y_label_values = self.get_y_label_values()
        y_label_span = max(y_label_values) - min(y_label_values)

        field_height /= float(y_label_span) or 1
        field_width = self.field_width()

        prev_sum = [0] * len(self.fields)
        cum_sum = [-min_value] * len(self.fields)

        coord_format = lambda c: '%(x)s %(y)s' % c
        lines = node(self.graph, "g", {'class': 'lines'})
        for line_n, data in reversed(list(enumerate(self.data))):
            if not self.stacked:
                cum_sum = [-min_value] * len(self.fields)

            cum_sum = map(add, cum_sum, data['data'])
            get_coords = lambda (i, val): self.calc_coords(
                i, val, field_width, field_height)
            coords = map(get_coords, enumerate(cum_sum))
            paths = map(coord_format, coords)
            line_path = ' '.join(paths)
            linegroup = node(lines, "g", {'class': 'linegroup%d' % line_n})

            if self.area_fill:
                # to draw the area, we'll use the line above, followed by
                #  tracing the bottom from right to left
                if self.stacked:
                    prev_sum_rev = list(enumerate(prev_sum)).reversed()
                    coords = map(get_coords, prev_sum_rev)
                    paths = map(coord_format, coords)
                    area_path = ' '.join(paths)
                    origin = paths[-1]
                else:
                    area_path = "V%s" % self.graph_height
                    origin = coord_format(get_coords((0, 0)))

                node(linegroup, 'path', {
                    'class': 'fill fill%s' % line_n,
                    'd': ' '.join(
                        ('M', origin, 'L', line_path, area_path, 'Z')),
                })

            # now draw the line itself
            node(linegroup, 'path', {
                'd': 'M%s L%s' % (paths[0], line_path),
                'class': 'line line%s' % line_n,
                })
            dots = node(linegroup, "g",
                        {'class': 'dots'})
            if self.show_data_points or self.show_data_values:
                for i, value in enumerate(cum_sum):
                    dot = node(dots, "g",
                                 {'class': 'dot'})
                    if self.show_data_points:
                        node(
                            dot,
                            'circle',
                            {'class': 'dot%s' % line_n},
                            cx=str(field_width * i),
                            cy=str(self.graph_height - value * field_height),
                            r='5',
                        )
                    self.make_datapoint_text(
                        dot,
                        field_width * i,
                        self.graph_height - value * field_height - 6,
                        value + min_value
                    )
            prev_sum = list(cum_sum)
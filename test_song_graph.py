import song_graph
import get_dataset_data


def test_attribute_vertex_creation():
    graph = get_dataset_data.get_song_graph_from_decades({1970})
    attribute_quantifiers = ['very low', 'low', 'medium low', 'medium high', 'high', 'very high']
    continuous_headers = song_graph.FLOAT_HEADERS.union(song_graph.INT_HEADERS)\
        .difference(song_graph.EXACT_HEADERS)

    continuous_headers.difference('key')

    for attribute_header in continuous_headers:
        print('spacer', attribute_header)
        for quantifier in attribute_quantifiers:
            attribute_label = quantifier + ' ' + attribute_header

            print(len(graph.get_vertex_by_item(attribute_label).neighbours))


if __name__ == '__main__':
    test_attribute_vertex_creation()




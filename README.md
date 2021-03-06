WikipediaPhilosophy
===================

The alt text of xkcd [903](http://xkcd.com/903) states: 

> Wikipedia trivia: if you take any article, click on the first link
> in the article text not in parentheses or italics, and then repeat,
>  you will eventually end up at "Philosophy".

This is a python script that tests and visualizes that using pygraphviz.

## Dependencies

* pygraphviz - http://networkx.lanl.gov/pygraphviz/
* BeautifulSoup - http://www.crummy.com/software/BeautifulSoup/

## Usage

    wiki.py [-i iterations] [-o outfile] [-p] [-l layout] [-s start]
            -i : iterations, default is 10
            -o : outfile, without the file extension. 
                 e.g. specifying '-o wiki' (the default)
                 will output wiki.log, wiki.dot, and wiki.png
                 if -p is specified
            -l : layout to be applied. One of 'twopi', 'neato', 
                 'dot', 'fdp'. 'dot' is the default. 
            -p : print graph as png.
            -s : url to start searching from. Must be of the form
                 /wiki/foo

## Examples

`wiki.py -p` will generate three files: wiki.log, wiki.dot, and wiki.png

`wiki.py -i 1 -s /wiki/xkcd -o xkcd -p` will perform 1 iteration starting at the xkcd wikipedia page. The output files will be xkcd.log, xkcd.dot, and xkcd.png

`wiki.py -i 100 -l twopi -p` will greate a graph in the twopi format using 100 iterations.

## Example Output

![example output](https://raw.github.com/jdtw/wikipediaphilosophy/master/example.png)

Generated with `wiki.py -p`.

## License

MIT

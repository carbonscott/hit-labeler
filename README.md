# Game of Hit

A GUI for labeling SPI hits.


## Install with `pip`

```
pip install git+https://github.com/carbonscott/hit-labeler --upgrade --user
```


## Dependency

```
pyqtgraph
numpy
```

## Shortcuts

- `N`: next query image
- `P`: prev query image
- `L`: label an image
- `G`: go to a specific image


## TODO

- [ ] Supports overwriting labels from a label file (e.g. csv).  
- [ ] Consider integrating `.xtc`, otherwise keep using `.cxi`.  `psana`
  converts raw `.xtc` into `.cxi`, so maybe it doesn't need to be integrated.  

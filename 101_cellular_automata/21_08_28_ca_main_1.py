lav = 20
width = 30
depth = 30

set_rules(224)

layer = Layer(width, depth, lav)

layer.print_life()

for i in range(lav, 0, -1):
    layer.set_neighbors()
    layer.set_lives()
    layer.draw_cells(i)

    layer.update()

    #layer.print_life()
    #print("\n")
    #layer.print_ne()
    #print("\n")


package Mapa;
import java.awt.Color;
import java.awt.Graphics;
import java.util.LinkedList;

class Nodo {
    private int x;
    private int y;
    private String osmid;
    private Color color = Color.blue; // Color original
    private int tamañoOriginal = 2;  // Tamaño original
    private boolean marcado = false;  // Indica si el nodo está marcado
    private LinkedList<Edge> Caminos = new LinkedList<>();
    int NODO_ANCHO = 20;
    int NODO_ALTO = 20;

    public Nodo(double x, double y, String osmid, double xv, double xv2, double yv, double yv2,int ancho, int alto) {
        this.x = escalarCoordenada(x, xv, xv2, 0, ancho);
        this.y = escalarCoordenada(y, yv, yv2, 0, alto);
        this.osmid = osmid;
    }

    public Color getColor() {
        return color;
    }

    public void setColor(Color color) {
        this.color = color;
    }

    public int getTamañoOriginal() {
        return tamañoOriginal;
    }

    public void setTamañoOriginal(int tamañoOriginal) {
        this.tamañoOriginal = tamañoOriginal;
    }

    public int getX() {
        return x;
    }

    public int getY() {
        return y;
    }

    public String getOsmid() {
        return osmid;
    }

    public boolean isMarcado() {
        return marcado;
    }

    public void nuevoCamino(Edge e) {
    	boolean existe = false;
    	if(Caminos.isEmpty()) {
    		Caminos.add(e);
    	}
    	else {
    		for(Edge ed: Caminos) {
    			if(ed.getOsmid().equalsIgnoreCase(e.getOsmid())) {
    				existe = true;
    			}
    		}
    		if(!existe) {
    			Caminos.add(e);
    		}
    	}
    }
	public void setMarcado(boolean marcado) {
        this.marcado = marcado;
       
     // Cambiar el tamaño del nodo cuando se marca
        if (marcado) {
            tamañoOriginal += 20; // Aumentar el tamaño original (por ejemplo, x3)
        } else {
            tamañoOriginal = 3; // Restaurar el tamaño original
        }
    }
	
	public void setDesmarcar() {
		if(marcado) {
			marcado = false;
			tamañoOriginal -= 20;
		}
	}

    public void dibujar(Graphics g, double zoom) {
        g.setColor(color);
        int scaledX = (int) this.x;
        int scaledY = (int) this.y;
        scaledX = (int) (scaledX * zoom);
        scaledY = (int) (scaledY * zoom);
        g.fillOval(scaledX - 1, scaledY - 1, tamañoOriginal, tamañoOriginal);
        g.setColor(Color.black);
    }

    private int escalarCoordenada(double valor, double rangoMinEntrada, double rangoMaxEntrada, int rangoMinSalida, int rangoMaxSalida) {
        return (int) (((valor - rangoMinEntrada) * (rangoMaxSalida - rangoMinSalida)) / (rangoMaxEntrada - rangoMinEntrada) + rangoMinSalida);
    }
}

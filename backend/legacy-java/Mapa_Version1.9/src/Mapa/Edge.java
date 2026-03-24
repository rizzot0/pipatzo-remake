package Mapa;
import java.awt.Color;
import java.awt.Graphics;

class Edge {
    //private String u;
    //private String v;
    private int k;
    private String osmid;
    private String name;
    private Nodo nodoFuente;
    private Nodo nodoDestino;

    public Edge(int k, String osmid, String name) {
        //this.u = u;
        //this.v = v;
        this.k = k;
        this.osmid = osmid;
        this.name = name;
    }
/*/
    public String getU() {
		return u;
	}



	public void setU(String u) {
		this.u = u;
	}



	public String getV() {
		return v;
	}



	public void setV(String v) {
		this.v = v;
	}
/*/


	public int getK() {
		return k;
	}



	public void setK(int k) {
		this.k = k;
	}



	public String getOsmid() {
		return osmid;
	}



	public void setOsmid(String osmid) {
		this.osmid = osmid;
	}


	public String getName() {
		return name;
	}



	public void setName(String name) {
		this.name = name;
	}



	public Nodo getNodoFuente() {
        return nodoFuente;
    }

    public void setNodoFuente(Nodo nodoFuente) {
        this.nodoFuente = nodoFuente;
    }

    public Nodo getNodoDestino() {
        return nodoDestino;
    }

    public void setNodoDestino(Nodo nodoDestino) {
        this.nodoDestino = nodoDestino;
    }


   
}
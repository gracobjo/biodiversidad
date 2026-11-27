"""Abre las fichas de GBIF desde un mapa Folium embebido en un cuaderno."""

from branca.element import Element

# El cuaderno pinta el mapa dentro de un iframe. Ese iframe no puede abrir
# ventanas, así que el clic se reenvía al documento del cuaderno, que sí abre el navegador.
# Si el HTML se abre como fichero, window.parent es la propia ventana y el enlace sigue su curso.
_SCRIPT_ENLACES = """
<script>
(function () {
  document.addEventListener("click", function (evento) {
    var nodo = evento.target;
    while (nodo && nodo.tagName !== "A") {
      nodo = nodo.parentElement;
    }
    if (!nodo || !nodo.href || window.parent === window) {
      return;
    }
    evento.preventDefault();
    evento.stopPropagation();
    try {
      var puente = window.parent.document.createElement("a");
      puente.href = nodo.href;
      puente.style.display = "none";
      window.parent.document.body.appendChild(puente);
      puente.click();
      puente.remove();
    } catch (error) {
      window.open(nodo.href, "_blank", "noopener");
    }
  }, true);
})();
</script>
"""


def activar_enlaces_externos(mapa) -> None:
    """Hace que los enlaces del popup abran GBIF aunque el mapa se vea dentro del cuaderno."""
    mapa.get_root().html.add_child(Element(_SCRIPT_ENLACES))

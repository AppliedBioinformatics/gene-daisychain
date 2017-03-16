function update_color_legend()
{
//$('#colorLegend span').text("Huhu");
var colorLegend = document.getElementById('colorLegend');
console.log("Update color legend");
var btn = document.createElement('button');
btn.setAttribute('type', 'button');
//btn.setAttribute('onclick', functions[i]);
btn.setAttribute('id', 'button' + "1");
colorLegend.appendChild(btn);
}
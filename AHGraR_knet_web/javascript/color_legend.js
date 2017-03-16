function update_color_legend(species_list)
{
//$('#colorLegend span').text("Huhu");
var colorLegend = document.getElementById('colorLegend');
console.log("Update color legend");
console.log(species_list);
var btn = document.createElement('button');
btn.setAttribute('type', 'button');
//btn.setAttribute('onclick', functions[i]);
btn.setAttribute('id', 'button' + "1");
btn.innerHTML = 'test value';
colorLegend.appendChild(btn);
}
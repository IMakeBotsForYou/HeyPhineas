$(document).on('click', '#invite_user', function(){
    $("#invite_user").prop("disabled", true);
    $("#invite_user_popup").fadeIn()
});

$(document).on('click', '#invite_user_close', function(){
    $("#invite_user").prop("disabled", false);
    $("#invite_user_popup").fadeOut()
});

var coll = document.getElementsByClassName("collapsible");
var i;

for (i = 0; i < coll.length; i++) {
  coll[i].addEventListener("click", function() {
    this.classList.toggle("active");
    var content = this.nextElementSibling;
    if (content.style.display === "block") {
      content.style.display = "none";
    } else {
      content.style.display = "block";
    }
  });
}
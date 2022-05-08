$(document).ready(function(){
    $(document).on('click', '#invite_user', function(){
        $("#invite_user").prop("disabled", true);
        $("#invite_user_popup").fadeIn()
    });

    $("#user_invite_close").on("click", function(){
        $("#invite_user_popup").fadeOut()
        $("#invite_user").prop("disabled", false);
    })

    $(document).on('click', '#add_loc_button', function(){
        $("#add_loc_button").prop("disabled", true);
        $("#add_loc_popup").fadeIn()
    });

    $(document).on('click', '#close_loc', function(){
        $("#add_loc_button").prop("disabled", false);
        $("#add_loc_popup").fadeOut()
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
});
var online_users = [];
var current_time;
var current_users_online = 0;

var party_users = [];
var friends = {

}
var lat = 0;
var lng = 0;
var socket = 0;

var party_text = '<h2 class="white">Party Members</h2> <button id="invite_user"><span class="fa fa-user-plus"></span></button><br><br>';
var members_text = "";
var in_party = false;
var leader_of_party = false;

//connect to the socket server.
socket = io.connect('http://' + document.domain + ':' + location.port + '/comms');

$(document).ready(function(){
    function update_party_members(data){
       var a = document.getElementById("members_panel")
       if (data.length == 0){
            return;
       }

       a.innerHTML = party_text;
       a.innerHTML += `<span style="color:red">${data[0]}</span><span style="color:white"> (owner)</span><br>`;
       leader_of_party = data[0] == user;
       if(leader_of_party){
        $("#start_origin").visibility = 'visible';
       }

       for(let i = 1; i < data.length; i++){
           a.innerHTML += `<p class="white">${data[i]}</p>`
       }
      a.style.visibility = 'visible';
    }

    if(window.location.href.split("/")[3] == '' || window.location.href.split("/")[3] == '#'){
        socket.emit('user_added_locations_get');
        socket.emit('party_members_list_get');
        socket.emit('online_members_get');

        // TEMP
        socket.emit('get_coords_of_party')

    }


    $(document).on('click', '#submit_place', function(){

        var type = document.getElementById("type").value;
        var radius = document.getElementById("radius").value;
        var min_rating = document.getElementById("min_rating").value;
        var limit = document.getElementById("limit").value;
        console.log();
        socket.emit('place_form_data', `${type}|${radius}|${min_rating}|${limit}`)
    });


    socket.on('party_members_list_get', function(data){
        update_party_members(data)
    });

    socket.on('online_members_get', function(data){
        online_users = data
        autocomplete(document.getElementById("invite_user_input"), users);
    });

    function ping_every_second(){
        let date = new Date;
        let hours = date.getHours();
        let minutes = "0" + date.getMinutes();
        let seconds = "0" + date.getSeconds();
        let formatTime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);
        $('#current_time').html(formatTime);
        socket.emit("ping", online_users);
    };
    const createClock = setInterval(ping_every_second, 1000);
    //update online user count
    socket.on('user_diff', function(msg) {
//        alert("User diff")
        if (typeof(msg.amount) != "undefined"){
            current_users_online = msg.amount;
        } else {
            console.log(current_users_online);
        }
        online_users = msg.names;
//        if (typeof(current_users_online) != "undefined"){
        $('#users_online').html(`${current_users_online} User(s) Online`);
//        }
//        else{
//        $('#users_online').html("You are logged in on another device.");
//        }

        // autofill
        $(function() {
            $("#user_to_invite").autocomplete({
                source: online_users,
                delay: 100,
            });
        });

    });

    socket.on('update_party_members', function(data){
       update_party_members(data);
    });

    socket.on('friend_data', function(data){
        console.log(data)
        function addtofriends(name, online){
            friends[name] = online;
        }
        for (var name in data['online']) {
            addtofriends(name, true);
        }
        for (var name in data['offline']) {
            addtofriends(name, false);
        }
        listhtml = '<h1 style="foreground: black;">Online</h1>'
        for (var friend in data['online']){
            listhtml += "<br>" + friend
        }
        listhtml += '<br><br><h1 style="foreground: gray;">Offline</h1>;'
        for (var friend in data['offline']){
            listhtml += "<br>" + friend
        }

        $("#friendslist").hmtl = listhtml;
    });

    //update notification count
    var notifs = 0;
    socket.on('notif', function(msg) {
        notifs += 1;
        $('#inbox').html(`Inbox (${notifs})`);
    });

    socket.on('reset_notifs', function(msg) {
        notifs = 0;
        $('#inbox').html(`Inbox`);
    });

    socket.on('best_3_locations', function(msg) {
        $('#recommended').html(msg);
    });
    socket.on('reset_first', function(msg) {
        first=false;
    });



    $("#create_party").on("click", function() {
        var a = document.getElementById("members_panel")
        if (!in_party){
           update_party_members([user])
           socket.emit("joined", "__self__");
           a.style.visibility = 'visible';
       } else {
           in_party = false;
           leader_of_party = false;
           socket.emit("left_party", 'foo');
           a.innerHTML = party_text;
           a.style.visibility = 'hidden';
           party_users=[];
        }
    });
    $("#confirm_invite").on("click", function() {
        var invite_user_input = document.getElementById("invite_user_input")
        socket.emit('invite_user', invite_user_input.value);
        console.log(invite_user_input.value);
        $("#invite_user_popup").fadeOut()
        $("#invite_user").prop("disabled", false);
    });

     $("#confirm_loc").on("click", function() {
        var name = document.getElementById("add_loc_name").value;
        var lat = document.getElementById("add_loc_lat").value;
        var lng = document.getElementById("add_loc_lng").value;
        socket.emit('add_location', `${name}, ${lat}, ${lng}`);
        $("#add_loc_button").fadeOut();
        $("#invite_user").prop("disabled", false);
    });


});
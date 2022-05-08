var online_users = [];
var current_time;
var online_users_num = 0;

var party_users = [];
var friends = {

}
var lat = 0;
var lng = 0;
var socket = io.connect('http://' + document.domain + ':' + location.port + '/comms');
//var party_text = '<h2 class="white">Party Members</h2> <button id="invite_user"><span class="fa fa-user-plus"></span></button><br><br>';
var members_text = "";
var in_party = false;
var leader_of_party = false;

//connect to the socket server.
//chat_socket = io.connect('http://' + document.domain + ':' + location.port + '/chatrooms');

$(document).ready(function(){
    function update_party_members(data){
       var a = document.getElementById("party-members")
       a.innerHTML = "";
       if (data.length == 0){
            in_party = false;
            leader_of_party = false;
            party_users = [];
            return;
       }
       in_party = true;
       a.innerHTML += `<div class="hover:bg-gray-light rounded"><span style="color:red">${data[0]}</span><span style="color:white"> (owner)</span><br></div>`;
       leader_of_party = data[0] == user;
       if(leader_of_party){
        $("#start_origin").visibility = 'visible';
       }

       for(let i = 1; i < data.length; i++){
           a.innerHTML += `<div class="hover:bg-gray-light rounded"><p class="white">${data[i]}</p></div>`
       }
      a.style.visibility = 'visible';
    }

    if(window.location.href.split("/")[3] == '' || window.location.href.split("/")[3] == '#'){
        socket.emit('user_added_locations_get');
        socket.emit('party_members_list_get');
        socket.emit('online_members_get');
        socket.emit('get_destination')
        // TEMP
        socket.emit('get_coords_of_party')
    }


//
//    $(document).on('click', '#submit_place', function(){
//
//        var type = document.getElementById("type").value;
//        var radius = document.getElementById("radius").value;
//        var min_rating = document.getElementById("min_rating").value;
//        var limit = document.getElementById("limit").value;
//        console.log();
//        socket.emit('place_form_data', `${type}|${radius}|${min_rating}|${limit}`)
//    });
//

    socket.on('party_members_list_get', function(data){
        update_party_members(data)
    });

    socket.on('online_members_get', function(data){
        online_users = data
        if(user == "Admin"){
//        document.getElementById("users_admin_list").innerHTML = "";
//            for(let i = 0; i < online_users.length; i++){
//                document.getElementById("users_admin_list").innerHTML += `<a>${online_users[i]}</a><b>`;
//            }
        } else {
            autocomplete(document.getElementById("invite_user_input"))
        }
//        autocomplete(document.getElementById("invite_user_input"), online_users);
    });


//    function add_listener_chat(element){
//        element.onclick = function(event){
//            chat_room_name = element.id.split("_")[0];
//            document.getElementById("chatroom-name").innerHTML = chat_room_name;
//            chatroom_element = document.getElementById("chat_room_messages");
//            chatroom_element.innerHTML = "";
//            for(let i = 0; i < chat_histories[chat_room_name].length; i++){
//                 var message = chat_histories[chat_room_name][i]["message"];
//                 var author =  chat_histories[chat_room_name][i]["author"];
//                 chatroom_element.innerHTML += `<p style="order: ${i};">${author}: {message}</p>`;
//            }
//            openChatTab(event)
//        };
//    }
//
//    var collection = document.getElementsByClassName("button-40");
//    var arr = Array.prototype.slice.call( collection, 0 );
//
//    arr.forEach(element => add_listener_chat(element));
//
//    for (let i = 0; i < collection.length; i++) {
//      collection[i].style.backgroundColor = "red";
//    }

    function ping_every_second(){
        let date = new Date;
        let hours = date.getHours();
        let minutes = "0" + date.getMinutes();
        let seconds = "0" + date.getSeconds();
        let formatTime = hours + ':' + minutes.substr(-2) + ':' + seconds.substr(-2);
//        $('#current_time').html(formatTime);
        socket.emit("ping", online_users);
    };

    const createClock = setInterval(ping_every_second, 1000);
    //update online user count
    socket.on('user_diff', function(msg) {
//        alert("User diff")
//        console.log(msg);
        if (typeof(msg.length) != "undefined"){
            online_users_num = msg.length;
        } else {
//            console.log(online_users_num);
        }
        online_users = msg;
        $('#users_online').html(`${online_users_num} User(s) Online`);
        autocomplete(document.getElementById("invite_user_input"))

        // autofill
//        $(function() {
//            $("#user_to_invite").autocomplete({
//                source: online_users,
//                delay: 100,
//            });
//        });

    });

    socket.on('all_users', function(data){
        var d = document.getElementById('user_data');
        d.innerHTML = `Online users (${online_users_num}) <br>`;
        Object.keys(data).forEach(function(name) {
            var online = data[name];
            d.innerHTML += `<p class="my-2 mx-2 rounded hover:bg-gray-light"><span style="color: ${online?'green':'red'};">${online?'+':'-'}</span> ${name}</p>`
        });


    });
    socket.on('update_party_members', function(data){
       update_party_members(data);
    });

    socket.on('friend_data', function(data){
//        console.log(data)
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



    socket.on('best_3_locations', function(msg) {
        $('#recommended').html(msg);
    });
    socket.on('reset_first', function(msg) {
        first=false;
    });



//    $("#create_party").on("click", function() {
//        var a = document.getElementById("members_panel")
//        if (!in_party){
//           update_party_members([user])
//           socket.emit("joined", "__self__");
//           a.style.visibility = 'visible';
//       } else {
//           in_party = false;
//           leader_of_party = false;
//           socket.emit("left_party", 'foo');
//           a.innerHTML = party_text;
//           a.style.visibility = 'hidden';
//           party_users=[];
//        }
//    });
    $("#confirm_invite").on("click", function() {
        var invite_user_input = document.getElementById("invite_user_input")
        socket.emit('invite_user', invite_user_input.value);
//        console.log(invite_user_input.value);
        $("#invite_user_popup").fadeOut()
        $("#invite_user").prop("disabled", false);
    });
     $("#confirm_loc").on("click", function() {
        var name = document.getElementById("add_loc_name").value;
        var lat = document.getElementById("add_loc_lat").value;
        var lng = document.getElementById("add_loc_lng").value;
        var type = document.getElementById("add_loc_type").value;
        socket.emit('add_location', `${name}, ${lat}, ${lng}, ${type}`);
        $("#add_loc_button").fadeOut();
        $("#invite_user").prop("disabled", false);
    });
    $('#reset_locs').on("click", function() {
        socket.emit('reset_locations');
    });

});
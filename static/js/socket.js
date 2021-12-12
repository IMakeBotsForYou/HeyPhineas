var online_users = [];
var current_time;
var current_users_online = 0;

var party_users = [];
var friends = {

}
var socket = null;

var in_party = false;
var leader_of_party = false;




$(document).ready(function(){
    //connect to the socket server.
    socket = io.connect('http://' + document.domain + ':' + location.port + '/comms');

//    timesocket.on('current time', function(msg) {
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
        online_users = msg.names;
        console.log(current_users_online);
        }
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

    $("#create_party").on("click", function() {
         if (!in_party){
            in_party = true;
            leader_of_party = true;
            user_to_invite = $("user_to_invite").val()
            socket.emit("joined", "__self__|" + user_to_invite);
        } else {
        //temporary
            in_party = false;
            leader_of_party = false;
            socket.emit("left_party", 'foo');
        }
    });

});
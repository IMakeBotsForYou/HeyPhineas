var chat_histories = {"Global": []}

function openChatTab(evt) {
  var i, tablinks;
  tablinks = document.getElementsByClassName("button-40");
  for (i = 0; i < tablinks.length; i++) {
    tablinks[i].className = tablinks[i].backgroundColor = "#111827";
  }
  evt.currentTarget.backgroundColor = "#777";
}

socket.on('message', function(data){
    var room = data["room"];
    console.log(data);
    chat_histories[room].push({"author": data["author"], "message": data["message"]});
    var chatroom = document.getElementById("invite_user_input");
    if(document.getElementById("chatroom-name").innerHTML == room){
        chatroom_element = document.getElementById("chat_room_messages");
        chatroom_element.innerHTML = "";
        for(let i = 0; i < chat_histories[room].length; i++){
             var message = chat_histories[room][i]["message"];
             var author =  chat_histories[room][i]["author"];
             chatroom_element.innerHTML += `<p class="white" style="left: 5%; order: ${i}; text-align: left; width:100%;">${author}: ${message}</p>`;
        }
    }
});
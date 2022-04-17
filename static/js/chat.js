var chat_histories = {"0": {"name": "Global", "history":[]}}
var current_chat = "0";
$(document).ready(function(){

function openChatTab(target_tab) {
  var i, tab_links;
  tab_links = document.getElementsByClassName("tab_button");
  for (i = 0; i < tab_links.length; i++) {
    tab_links[i].className = tab_links[i].className.replace("_active", "_inactive");
  }
  target_tab.className = target_tab.className.replace("_inactive", "_active")
  current_chat = target_tab.title;
  chatroom_element = document.getElementById("chat_room_messages");
  chatroom_element.innerHTML = "";
  for(let i = 0; i < chat_histories[current_chat].history.length; i++){
    var message = chat_histories[current_chat].history[i]["message"];
    var author =  chat_histories[current_chat].history[i]["author"];
    chatroom_element.innerHTML += `<p class="left-[5%] mb-[5px] order-[${i}] text-left text-white w-[100%]">${author}: ${message}</p>`;
  }
}

var tablinks = Array.from(document.getElementsByClassName("tab_button"));
tablinks.forEach(function(item){
    item.addEventListener('click', function(event, a){
        openChatTab(item);
    }, false);
});


socket.on('create_chat', function(data){
    if(!(data["id"] in chat_histories)){
        chat_histories[data["id"]] = {"name": data["name"], "history": data["history"], "members": data["members"]}
        var tabs = document.getElementById('tabs');
        tabs.innerHTML += `<button class="my-2 tab_button _inactive" title="${data['id']}" type="button">${data["name"]}</button>`
    }
});

socket.on('message', function(data){
    var room = data["id"];
    chat_histories[room].history.push({"author": data["author"], "message": data["message"]});
    if(current_chat == room){
        chatroom_element = document.getElementById("chat_room_messages");
        chatroom_element.innerHTML = "";
        for(let i = 0; i < chat_histories[room].history.length; i++){
             var message = chat_histories[room].history[i]["message"];
             var author =  chat_histories[room].history[i]["author"];
             chatroom_element.innerHTML += `<p class="left-[5%] mb-[5px] order-[${i}] text-left text-white w-[100%]">${author}: ${message}</p>`;
        }
    }
});
document.getElementById('chat_input_area').addEventListener('keydown', function(e) {
    var input = document.getElementById('chat_input_area');
    var text = "";
    if(e.key === "Enter" || e.keyCode == 13) {
        text = input.value;
        if (text == "")
            return;
        console.log(current_chat);
        socket.emit('chat_message', {"message": text, "room": current_chat});
        input.value = "";
    }
});
});
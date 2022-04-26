var chat_histories = {}
var current_chat = "0";

$(document).ready(function(){

function openChatTab(target_tab) {
  var i, tab_links;
  var tab_element = document.getElementById('tabs');
  var tab_links = Array.from(tab_element.querySelectorAll(".tab_button"));
//  console.log(tab_links, tab_element);
  for (i = 0; i < tab_links.length; i++) {
    tab_links[i].className = tab_links[i].className.replace("_active", "_inactive");
  }
  target_tab.className = target_tab.className.replace("_inactive", "_active");
  current_chat = target_tab.id.slice(5, target_tab.id.length);
  loadChat(current_chat);
}

function update_tabs(){
    var tab_element = document.getElementById('tabs')
    var tablinks = Array.from(tab_element.querySelectorAll(".tab_button"));
    tablinks.forEach(function(item){
        console.log(1, item);
        item.addEventListener('click', function(event, a){
            openChatTab(item);
        }, false);
    });
}

function loadChat(room){
    chatroom_element = document.getElementById("chat_room_messages");
    var base = `<p class="mx-[5px] mb-[5px] text-left text-white w-[95%] hover:bg-gray-light rounded-md">`
    console.log(room);
    chatroom_element.innerHTML = chat_histories[room].history //get history
                                .slice(0).reverse()  // reverse array
                                .map(message => `${base}${message["author"]}: ${message["message"]}</p>`) // map array to messages
                                .join("");  //join into one string
}
update_tabs();
socket.on('create_chat', function(data){
    chat_histories[data["id"]] = {"name": data["name"], "history": data["history"], "members": data["members"]};
    var tabs = document.getElementById('tabs');
    tabs.innerHTML += `<button class="my-2 tab_button _inactive" id="chat_${data['id']}" type="button">${data["name"]}</button>`;

    update_tabs();
    socket.emit('confirm_chat', data["id"])
    if (Object.keys(chat_histories).length == 1){
       globalChat = document.getElementById(`chat_0`);
       openChatTab(globalChat);
    }
});

socket.on('del_chat', function(chat_id){
   delete chat_histories.chat_id;
   var chat_tab = document.getElementById(`chat_${chat_id}`);
   chat_tab.parentNode.removeChild(chat_tab);
   socket.emit('confirm_del_chat', chat_id);
   globalChat = document.getElementById(`chat_0`);
   openChatTab(globalChat);
});

socket.on('message', function(data){
    var room = data["id"];
    chat_histories[room].history.push({"author": data["author"], "message": data["message"]});
    if(current_chat == room){
        loadChat(room);
    }
});

document.getElementById('chat_input_area').addEventListener('keydown', function(e) {
    var input = document.getElementById('chat_input_area');
    var text = "";
    if(e.key === "Enter" || e.keyCode == 13) {
        text = input.value;
        if (text == "")
            return;
        socket.emit('chat_message', {"message": text, "room": current_chat});
        input.value = "";
    }
});
});
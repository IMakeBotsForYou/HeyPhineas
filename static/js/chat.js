var chat_histories = {}
var current_chat = "0";

$(document).ready(function(){
if (user == "Admin"){
return;
}
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
//        console.log(1, item);
        item.addEventListener('click', function(event, a){
            openChatTab(item);
        }, false);
    });
}

function loadChat(room){
    chatroom_element = document.getElementById("chat_room_messages");
    var base = `<p class="mx-[5px] mb-[5px] text-left text-white w-[95%] hover:bg-gray-light rounded-md">`
//    console.log(room);
    chatroom_element.innerHTML = chat_histories[room].history //get history
                                .slice(0).reverse()  // reverse array
                                .map(message => `${base}${message["author"]}: ${message["message"]}</p>`) // map array to messages
                                .join("");  //join into one string
    var tab_name = document.getElementById(`chat_${room}`).innerHTML;
    var start_bracket_index = tab_name.indexOf("(");
    // removes " (number)"
    if (start_bracket_index != -1){
        tab_name = tab_name.slice(0, start_bracket_index-1);
        document.getElementById(`chat_${room}`).innerHTML = tab_name;
    }

}

update_tabs();
socket.on('create_chat', function(data){
    if(!(data["id"] in chat_histories)){
    var tabs = document.getElementById('tabs');
    tabs.innerHTML += `<button class="my-2 tab_button _inactive" id="chat_${data['id']}" type="button">${data["name"]}</button>`;
    }
    chat_histories[data["id"]] = {"name": data["name"], "history": data["history"], "members": data["members"]};

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
    if (!(room in chat_histories))
        return;
    chat_histories[room].history.push({"author": data["author"], "message": data["message"]});
    var tab_name = document.getElementById(`chat_${room}`).innerHTML;
//    console.log(tab_name, current_chat == room, current_chat, room);
    if(current_chat == room){
        loadChat(room);
    } else {
        // make it say TABNAME (1)
        if(tab_name[tab_name.length-1] == ")"){
            // already has the notification thing
            var start_bracket_index = tab_name.indexOf("(");
            var number = parseInt(tab_name.slice(start_bracket_index+1, tab_name.length-1));
            tab_name = tab_name.slice(0, start_bracket_index) +`(${number+1})`;
//            console.log(tab_name.slice(0, start_bracket_index), start_bracket_index, number, tab_name);
        } else {
            tab_name += " (1)";
//            console.log(tab_name);
        }
    }
    document.getElementById(`chat_${room}`).innerHTML = tab_name;
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
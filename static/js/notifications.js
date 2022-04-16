$(document).ready(function(){
    socket.on('inbox_update', function(data){
        var amount = data[0];
        var messages = data[1];

        if (amount == 0){
            $('notification_autogenerated_div').html(`<h1 class="white">No messages</h1>`);
            return;
        }

        var final_string = "";

        for (let i = 0; i < messages.length; i++) {
            var id = messages[i].id;
            var title = messages[i].title;
            var content = messages[i].content;
            var sender = messages[i].sender;
            var type = messages[i].type;

            final_string += `
            <div class="mb-[10px]">
                <button type="button" class="collapsible mb-1" style="">${title}</button>
                <div class="content white" style="display: none;">
                    <div><p id="message_content_${id}" style="margin: 0 0 14px 0;"><b>Message from ${sender}:</b><br>${content}</p></div>
                        <div style="margin: 0 auto; text-white">
            `

            if (type == "simple_question"){
                final_string += `
                    <button type="button" class="form_button mb-[10px] bg-white text-black hover:text-white hover:bg-black transition-300" id="confirm-button_${id}" >Accept</button>
                            <script>
                            document.getElementById("confirm-button_${id}").addEventListener("click", function() {
                               socket.emit('inbox_notification_react', {"message_id": ${id}, "reaction": "accept"});
                            });
                            </script>
                `
            }
            if (type == "group_suggestion"){
                final_string += `
                    <button type="button" class="form_button mb-[10px] bg-white text-black hover:bg-black hover:text-white transition-300" id="accept-suggestion-button_${id}" >Accept</button>
                    <button type="button" class="form_button mb-[10px] bg-white text-black hover:bg-black hover:text-white transition-300" id="reject-button_${id}" >Mark as read</button>
                        <script>
                        // accept suggestion made by server
                        console.log(type);
                        document.getElementById("accept-suggestion-button_${id}").addEventListener("click", function() {
                           socket.emit('inbox_notification_react', {"message_id": ${id}, "reaction": "accept_suggestion"});
                        });
                        console.log(document.getElementById("accept-suggestion-button_${id}"));
                        // reject suggestion made by server
                        document.getElementById("reject-button_${id}").addEventListener("click", function() {
                           socket.emit('inbox_notification_react', {"message_id": ${id}, "reaction": "reject_suggestion"});
                        });
                        </script>
            `
            } else {
                final_string += `
                    <button type="button" class="form_button mb-[10px] bg-white text-black hover:bg-black hover:text-white transition-300" id="close-button_${id}" >Mark as read</button>
                    <script>
                        document.getElementById("close-button_${id}").addEventListener("click", function() {
                           socket.emit('inbox_notification_react', {"message_id": ${id}, "reaction": "ignore"});
                        });
                    </script>
                `
            }

            final_string +=`
                </div>
                    </div>
                <script>
                    var x = document.getElementById("message_content_${id}");
                    x.innerHTML = \`Message from ${sender}:</b><br>${content}</p>\`.replace("\\n", "<pre>").replace("\n", "<pre>");
                </script>
            </div>
            `
        }

        document.getElementById('notification_autogenerated_div').innerHTML = final_string;
        var coll = document.getElementsByClassName("collapsible");
        var i;
        for (i = 0; i < coll.length; i++) {
          coll[i].addEventListener("click", function() {
            this.classList.toggle("active");
            var content = this.nextElementSibling;
            if (content.style.display == "block") {
              content.style.display = "none";
            } else {
              content.style.display = "block";
            }
          });
        }
    });

//    socket.on('notifications', function(data){
//        var amount = data;
//        if (amount != 0)
//            $('#inbox').html(`Inbox (${amount})`);
//        else
//            $('#inbox').html(`Inbox`);
//    });
});

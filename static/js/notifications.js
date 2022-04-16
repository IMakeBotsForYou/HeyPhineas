$(document).ready(function(){
    socket.on('notifications', function(data) {
        if (data != 0)
            $('#inbox').html(`Inbox (${data})`);
        else
            $('#inbox').html(`Inbox`);
    });
});
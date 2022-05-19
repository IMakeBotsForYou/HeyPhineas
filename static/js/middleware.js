function validate_message(data){
//        message_id = data["__message_id"]
//        socket.emit('confirm_message', message_id);
//        if (message_ids.includes(message_id)){
//            message_ids.push(message_id);
//            return {"status": "already_received"};
//        } else {
//        data = data["__payload"];
        return {"status": "new", "data": data};
//        }
}
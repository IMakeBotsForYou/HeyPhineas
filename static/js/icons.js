//const icon_key = "8d9db97895f80c96bc468c7a5e55b58f003e3456";
////
//var headers = {
//  'Content-Type':'multipart/form-data',
//  'Accept':'application/json',
//  'apikey':icon_key,
//};
//
//$.ajax({
//  url: 'https://api.flaticon.com/v3/app/authentication',
//  method: 'post',
//  dataType: 'json',
//
//  headers: headers,
//  success: function(data) {
//    console.log(JSON.stringify(data));
//  }
//})


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


icons = {
"park": "https://cdn-icons-png.flaticon.com/32/1175/1175062.png",
"gas": "https://cdn-icons-png.flaticon.com/32/483/483497.png",
"gas station": "https://cdn-icons-png.flaticon.com/32/483/483497.png",
"food": "https://cdn-icons-png.flaticon.com/32/685/685352.png",
"restaurant": "https://cdn-icons-png.flaticon.com/32/685/685352.png"
}
function get_icon(name){
    if (name in icons)
       return icons[name]
    else
       return "https://cdn-icons.flaticon.com/png/512/2697/premium/2697390.png"
}//
//var headers = {
//  'Accept':'application/json',
//  'Authorization':icon_key
//};
//function get_icons(orderBy){
//    $.ajax({
//      url: 'https://api.flaticon.com/v3/search/icons/',
//      method: 'get',
//      data: '?q=' + orderBy,
//      limit: 1,
//      headers: headers,
//      success: function(data) {
//        console.log(JSON.stringify(data));
//      }
//    });
//}

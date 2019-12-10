
$(function () {
    var websocket;
    if('WebSocket' in window){
        console.log("WebSocket");
        websocket = new WebSocket("ws://127.0.0.1:8000/ws/chat/");
    } else if ('MozWebSocket' in window){
        websocket = new MozWebSocket("ws://127.0.0.1:8000/ws/chat/");
    } else {
        websocket = new SockJS("ws://127.0.0.1:8000/ws/chat/");
    }
    console.log("create succeed");
    websocket.onopen = function(event) {
        console.log("connect succeed");
    };

    // send message
    $("#chat-send").click(function () {
        var textContent = $(".div-textarea").html().replace(/[\n\r]/g, '<br>')
        if (textContent != "") {
            var header_show_im = document.getElementById("header_show_img");
            console.log(header_show_im);
            $(".chatBox-content-demo").append("<div class=\"clearfloat\">" +
                "<div class=\"author-name\"></div> " +
                "<div class=\"right\"> <div class=\"chat-message\"> " + textContent + " </div> " +
                "<div class=\"chat-avatars\"><img src=\""+header_show_im.src+"\" alt=\"photo\" /></div> </div> </div>");
            // clear input
            $(".div-textarea").html("");
            //default move to the bottom of chat box
            $(document).ready(function () {
                $("#chatBox-content-demo").scrollTop($("#chatBox-content-demo")[0].scrollHeight);
            });
            if(!websocket){
                alert("Please connect server.");
            } else{
                websocket.send(JSON.stringify({'title': 'client message', 'data': textContent, 'url': null}));
            }
        }
    });

    // receive message from backend
    websocket.onmessage = function(event){
        var data =JSON.parse(event.data);
        console.log(data);
        $(".chatBox-content-demo").append("<div class=\"clearfloat\">" +
                "<div class=\"author-name\"></div> " +
                "<div class=\"left\"> <div class=\"chat-avatars\"><img src=\"../static/images/chatbot_logo.jpg\" alt=\"photo\" /></div> " +
                "<div class=\"chat-message\"> " + data['data'] + " </div> </div> </div>");
    }

    // error
    websocket.onerror = function(event){
        console.log(event);
    }

    // websocket close
    websocket.onclose = function(event){
        alert("chat interrupted please reload again")
    }

});

// chatbox
screenFuc();
function screenFuc() {
    var topHeight = $(".chatBox-head").innerHeight();
    
    var winWidth = $(window).innerWidth();
    if (winWidth <= 768) {
        var totalHeight = $(window).height(); 
        $(".chatBox-info").css("height", totalHeight - topHeight);
        var infoHeight = $(".chatBox-info").innerHeight();
        
        $(".chatBox-content").css("height", infoHeight - 46);
        $(".chatBox-content-demo").css("height", infoHeight - 46);

        $(".chatBox-list").css("height", totalHeight - topHeight);
        $(".chatBox-kuang").css("height", totalHeight - topHeight);
        $(".div-textarea").css("width", winWidth - 106);
    } else {
        $(".chatBox-info").css("height", 495);
        $(".chatBox-content").css("height", 448);
        $(".chatBox-content-demo").css("height", 448);
        $(".chatBox-list").css("height", 495);
        $(".chatBox-kuang").css("height", 495);
        $(".div-textarea").css("width", 260);
    }
}
(window.onresize = function () {
    screenFuc();
})();

var totalNum = $(".chat-message-num").html();
if (totalNum == "") {
    $(".chat-message-num").css("padding", 0);
}
$(".message-num").each(function () {
    var wdNum = $(this).html();
    if (wdNum == "") {
        $(this).css("padding", 0);
    }
});

$(".chatBox").toggle(10);

// open/close chat window
$(".chatBtn").click(function () {
    $(".chatBox").toggle(10);
})
$(".chat-close").click(function () {
    $(".chatBox").toggle(10);
})
// open chat 
$(".chatBox-head-one").toggle();
$(".chatBox-head-two").toggle();
$(".chatBox-list").fadeToggle();
$(".chatBox-kuang").fadeToggle();

//send name
$(".ChatInfoName").text($(this).children(".chat-name").children("p").eq(0).html());

//send user photo
$(".ChatInfoHead>img").attr("src", $(this).children().eq(0).children("img").attr("src"));

//to the bottom of chat box
$(document).ready(function () {
    $("#chatBox-content-demo").scrollTop($("#chatBox-content-demo")[0].scrollHeight);
});
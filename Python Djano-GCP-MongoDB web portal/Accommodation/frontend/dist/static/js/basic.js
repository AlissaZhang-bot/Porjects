$(document).on('submit', '#loginForm', function(){
    var username =  $("#uName").val(); // 获取输入框的值
    var password =  $("#uPass").val();
    $.post(
        '{% url 'login' %}',  
        // data
        {
            "username": username,
            "password": password
        },  
        // callback
        function(json){
            //sessionStorage.setItem('username', username);
            var status = json['status'];
            if(status === "succeed"){
                $("#regist-box").hide();
                $("#signin-icon").hide();
                $("#welcome").text(username);
                $("#header_show_img").attr('src', json['img']);
            }else{
                var msg = json['msg'];
                $("#my-account").hide();
                $("#login-message").text(msg);
            }
        },
    )
    return false;
});
// Signup
$(document).on('submit', '#signupForm', function(){
    var username =  $("#signup_uName").val(); // 获取输入框的值
    var password =  $("#signup_uPass").val();
    var password2 =  $("#signup_uPass2").val();
    $.post(
        '{% url 'signup' %}',  
        // data
        {
            "username": username,
            "password": password,
            "password2": password2
        },  
        // callback
        function(json){
            var status = json['status'];
            if(status === "succeed"){
                $("#regist-box").hide();
                $("#signin-icon").hide();
                $("#welcome").text(username);
            }else{
                var msg = json['msg'];
                $("#my-account").hide();
                $("#signup-message").text(msg);
            }
        },
    )
    return false;
});
// logout
$(document).on('click', '#logout-link', function(){
    $.get(
        '{% url 'logout' %}',  
        // data
        {},  
        // callback
        function(json){
            $("#signin-icon").show();
            $("#welcome").removeClass().addClass("header-user-name");
            $("#welcome-list").removeClass();
            $("#welcome").text("My Account");
        },
    )
});
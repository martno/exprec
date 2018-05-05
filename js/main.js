"use strict";


$( document ).ready(function() {
    loadMain([], ['archive']);

    $('.button-archive').click(function() {
        $('.experiment-row').each(function() {
            if ($(this).is(':checked')) {
                var checkboxId = $(this).attr('id');
                var id = checkboxId.replace('checkbox-', '');
                var promise = postJson('/add_tags/' + id, ["archive"]);
            }
        });
    });

    $('#show-inbox').click(function() {
        loadMain([], ['archive']);
    });

    $('#show-archive').click(function() {
        loadMain(['archive'], []);
    });
});


function loadMain(whitelist, blacklist) {
    var promise = postJson('/experiment-table', {
        'whitelist': whitelist,
        'blacklist': blacklist
    });

    promise.done(function(content) {
        $('#experiment-table').html(content);
        console.log('#experiment-table loaded!');

        $(".experiment-button").click(function() {
            var buttonId = $(this).attr('id');
            console.log(buttonId);

            var id = buttonId.replace('button-', '');

            $('#experiments-div').load('/experiment/' + id, function() {
                $('#main').hide();
                $('.button-go-back').click(function() {
                    $('#main').show();
                    $('#experiments-div').html('');
                });
                
                highlightAllCode();
            });
        });
    });
}


function highlightAllCode() {
    $('pre > code').each(function() {
        hljs.highlightBlock(this);
        hljs.lineNumbersBlock(this);
   });
}


function postJson(url, data) {
    var promise = $.ajax({
        type: "POST",
        url: url,
        data: JSON.stringify(data),
        contentType: 'application/json; charset=utf-8',
    });

    return promise;
}


function hasMethod(obj, method) {
    for (var id in obj) {
        if (typeof(obj[id]) == "function" && id === method) {
            return true;
        }
    }
    return false;
}


function getMethods(obj) {
    var result = [];
    for (var id in obj) {
      try {
        if (typeof(obj[id]) == "function") {
          result.push(id + ": " + obj[id].toString());
        }
      } catch (err) {
        result.push(id + ": inaccessible");
      }
    }
    return result;
}


var loadjs = function(rest_url, error_message) {
  rest_url = rest_url.slice(0, rest_url.length - 2);
  $('#all-messages-checkbox').change(function() {
    $('.message-checkbox').prop('checked', this.checked);
  });
  $('.show-modal-btn').click(function() {
    var msgid = $(this).data('msgid');
    $.ajax({
      url: rest_url + msgid,
      success: function(data) {
        $('#message-source-btn').attr('href', rest_url + msgid + '?raw')
        $('#message-title').html(data.subject);
        $('.modal-footer form input[name="msgid"]').attr('value', msgid);
        if (data.msg.body) {
          $('#held-message-content').text(data.msg.body);
        } else {
          $('#held-message-content').html('<p>Message content could not be extracted</p>');
        }
        attachments = '';
        for (i = 0; i < data.attachments.length; i++) {
          attachments += '<a href="' + data.attachments[i][0] + '">' + data.attachments[i][1] + '</a><br />'; 
        }
        if (attachments != '') {
          $('#held-message-attachment-header').removeClass('hidden');
          $('#held-message-attachments').html(attachments);
        }
        $('#held-message-content').html($('#held-message-content').html().replace(/\n/g, "<br />"));
        $('#held-message-headers').text(data.msg.headers);
        $('#held-message-headers').html($('#held-message-headers').html().replace(/\n/g, "<br />") + '<hr />');
        $('#held-messages-modal').modal('show');
      },
      error : function() {
        alert(error_message);
      },
      statusCode: {
        500: function() {
          alert(error_message);
        }
      }});
    return false;
  });
  $('#toggle-headers').click(function() {
    if ($(this).hasClass('active')) {
      $('#held-message-headers').addClass('hidden');
    } else {
      $('#held-message-headers').removeClass('hidden');
    }
  });
  $('#held-messages-modal').on('hidden.bs.modal', function() {
    $('#held-message-headers').addClass('hidden');
    $('#message-title').html('');
    $('#toggle-headers').removeClass('active');
    $('#held-message-attachment-header').addClass('hidden');
    $('#held-message-attachments').text('');
  });
}

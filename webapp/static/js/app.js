var areyousure = function(){
  return confirm('Are you sure?');
}

var getPulse = function(c_id){
  $('#pulse-'+c_id).html('<span class="label label-warning">Checking...</span>');
  $.ajax({
    url: '/pulse/' + c_id,
    type: "GET",
    success: function(data) {
      if (data.up) {
        $('#pulse-'+c_id).html('<span class="label label-success">Database up</span>');
      } else {
        $('#pulse-'+c_id).html('<span class="label label-danger">Database down</span>');
      }
    },
    dataType: "json",
    // check every 60 sec
    complete: setTimeout(function() {getPulse(c_id)}, 60000),
    timeout: 2000
  });
}

$(document).ready(function(){
  $.each($('.checkbox-server-up'), function(i, v){
    // wait 5 sec for the DB to warm-up
    setTimeout(function(){getPulse(v.id)}, 5000);
  });
});

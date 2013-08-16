var RUsure = function(){
  return confirm('Are you sure?');
}

var getPulse = function(c_id){
  $.get('/pulse/' + c_id, function(data){
    if (data.up) {
      $('#pulse-'+c_id).html('<span class="label label-success">Database up</span>');
    } else {
      $('#pulse-'+c_id).html('<span class="label label-danger">Database down</span>');
    }
    
    console.log(data);
  });
}

$(document).ready(function(){
  $.each($('.checkbox-server-up'), function(i, v){
    getPulse(v.id);
  });
});

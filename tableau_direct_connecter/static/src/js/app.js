var base_url = window.location.origin;

const types = {

  "bigint":tableau.dataTypeEnum.int,
  "decimal":tableau.dataTypeEnum.int,
  "smallint":tableau.dataTypeEnum.int,
  "serial":tableau.dataTypeEnum.int,
  "bigserial":tableau.dataTypeEnum.int,
  "boolean":tableau.dataTypeEnum.bool,
  "bytea":tableau.dataTypeEnum.int,
  "character varying":tableau.dataTypeEnum.string,
  "varchar":tableau.dataTypeEnum.string,
  "character":tableau.dataTypeEnum.string,
  "char":tableau.dataTypeEnum.string,
  "date":tableau.dataTypeEnum.string,
  "double precision":tableau.dataTypeEnum.float,
  "real":tableau.dataTypeEnum.float,
  "integer":tableau.dataTypeEnum.int,
  "numeric":tableau.dataTypeEnum.int,
  "text":tableau.dataTypeEnum.string,
  "timestamp without time zone":tableau.dataTypeEnum.string,
  "timestamp with time zone":tableau.dataTypeEnum.string,
  "time without time zone":tableau.dataTypeEnum.string,
  "time with time zone":tableau.dataTypeEnum.string

  }

  function binary_search_by_table_name(table, metadata) {
    let start = 0;
    let end = metadata.length - 1;
  
    while (start <= end) {
      let middle = Math.floor((start + end) / 2);
  
      if (metadata[middle].table === table) {
        return metadata[middle];
      } else if (metadata[middle].table < table) {
        start = middle + 1;
      } else {
        end = middle - 1;
      }
    }
    return -1;
  }

  function make_schema(object){
    var table_list = [];
    Object.entries(object).map(entry => {
        let key = entry[0];
        let value = entry[1];
        let schema_lst = [];
        for(let i = 0; i< value.length; i++)
        {
            schema_lst.push({id:value[i].column_name,dataType:types[value[i].column_type]})
        }
        table_list.push({id:key,columns:schema_lst})
        
    });
    
    return table_list
    
    }

(function () {
  var myConnector = tableau.makeConnector();
  
   

  myConnector.getSchema = function (schemaCallback) {
    var list = JSON.parse(tableau.connectionData);

    schemaCallback(list.schema);
  };

  myConnector.getData = function (table, doneCallback) {
    let list = JSON.parse(tableau.connectionData);
    let metadata = list.metadata
    let token = list.token
    let search_result = binary_search_by_table_name(table.tableInfo.id,metadata);
  
    
if (search_result == -1){
  tableau.reportProgress("Please Wait ...");
    var xhr = $.ajax({
      url: `${base_url}/model/${table.tableInfo.id}/`,
      method:"GET",
      headers:{'Authorization':token},
      async:false,
      statusCode: {
        401: function(responseObject, textStatus, jqXHR) {
          tableau.abortWithError("Access Token is Expired !");
        },
        500: function(responseObject, textStatus, errorThrown) {
          tableau.abortWithError("We got Internal Server Error");
        }
        ,
      404: function(responseObject, textStatus, errorThrown) {
        tableau.abortWithError(`${table.tableInfo.id} not found in your Database`);
      },
      408: function(responseObject, textStatus, errorThrown) {
        tableau.abortWithError("Your trial is expired !");
      }
                   
    },
      success: function (data) {
          if (data) {

              table.appendRows(data);
              doneCallback();

          }
          else {
              tableau.abortWithError("No results found");
          }
      },
      error: function (xhr, ajaxOptions, thrownError) {
        
      }
  });
}
else{
let current_call = 1;
let limit = 20000
let needed_call = Math.ceil(search_result.size/limit)
var last_id = 0
while(current_call <= needed_call)
{
  
  tableau.reportProgress("Getting rows from ID " + (last_id+1));
  var xhr = $.ajax({
    url: `${base_url}/model/${table.tableInfo.id}/?last_id=${last_id}`,
    method:"GET",
    headers:{'Authorization':token},
    async:false,
    statusCode: {
      401: function(responseObject, textStatus, jqXHR) {
        tableau.abortWithError("Access Token is Expired !");
      },
      500: function(responseObject, textStatus, errorThrown) {
        tableau.abortWithError("We got Internal Server Error");
      } ,
      404: function(responseObject, textStatus, errorThrown) {
        tableau.abortWithError(`${table.tableInfo.id} not found in your Database`);
      },
      408: function(responseObject, textStatus, errorThrown) {
        tableau.abortWithError("Your trial is expired !");
      }            
  },
    success: function (data) {
        if (data) {
          // console.log(data);
          last_id = data[data.length-1].id
          // console.log("last id "+last_id);
          table.appendRows(data);
          current_call+=1;
          
        }
        else {
            tableau.abortWithError("No results found");
            current_call+=1;
        }
    },
    error: function (xhr, ajaxOptions, thrownError) {
        current_call+=1;

        
    }
});


}
doneCallback();


}
   
  };
  tableau.registerConnector(myConnector);

  function validate_input_field(){
    if ($('#token').val().trim())
    {
      return true;
    }
    else{
      return false;
    }
  }

  // Create event listeners for when the user submits the form
  $(document).ready(function() {
    function add_exmlation_sign(cls){
      var fwasm = document.getElementById('f-icon')
      fwasm.className = cls;
      
              }
    

    $("#submit").click(function() {
       
      let required = validate_input_field();
      if(!required){
        
        add_exmlation_sign('fa fa-exclamation-triangle mr-1');
        document.getElementById("status").textContent = "Please Enter Access Token"
        $('#token').css('border-color', 'red');
        $('#status').css('color', 'red');

        return false
      }
      var jqxhr = $.ajax( {url:`${base_url}/schemas/`,
      headers:{"Authorization":$('#token').val().trim()},
      beforeSend: function(){
         
          $('#submit').text('Please Wait...').attr('disabled', true).addClass('bt-hud');

          
         
      },
      complete: function(){
         
          console.log("complete schema callback");
      }
      ,
      statusCode: {
        401: function(responseObject, textStatus, jqXHR) {
          add_exmlation_sign('fa fa-exclamation-triangle mr-1');
          document.getElementById("status").textContent = responseObject.responseJSON.message
          $('#status').css('color', 'red');

          $('#submit').text('Get Odoo Data').attr('disabled', false).removeClass('bt-hud')
        },
        500: function(responseObject, textStatus, errorThrown) {
          add_exmlation_sign('fa fa-exclamation-triangle mr-1');
          document.getElementById("status").textContent = "We have got the internal server error please check the server logs"
          $('#status').css('color', 'red');
        } ,
        408: function(responseObject, textStatus, jqXHR) {
          add_exmlation_sign('fa fa-exclamation-triangle mr-1');
          document.getElementById("status").textContent = responseObject.responseJSON.message
          $('#status').css('color', 'red');

          $('#submit').text('Get Odoo Data').attr('disabled', false).removeClass('bt-hud')
        }          
    }
      } )

      .done(function(response) {
        res = make_schema(response.schema);
        console.log(response.dbname);
        try {
        tableau.connectionData =JSON.stringify({schema: res,metadata:response.metadata,token:$('#token').val().trim()});
        tableau.connectionName = response.dbname;
        tableau.submit();
        }
        catch(err) {
          document.getElementById("status").innerHTML = "Tableau initialization is failed We are Unable to find WDC Environment";
          $('#status').css('color', 'red');

          $('#submit').text('Get Odoo Data').attr('disabled', false).removeClass('bt-hud');
          add_exmlation_sign('fa fa-ban fa-2x mr-1 mt-2');

        }
      })
      .fail(function(xhr, ajaxOptions, thrownError) {
        console.log( xhr );
        console.log( ajaxOptions );
        console.log( thrownError );
      })
      .always(function() {
      console.log( "second complete" );

       
      });
      
      
      
        
      
                 
    });
});

})();








  

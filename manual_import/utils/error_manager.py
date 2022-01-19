
class ErrorManager:

    def __init__(self):

        self._single_errors = False
        self._mult_errors = False

        self.mult_errors = {}
        self.dic = {"msg": "", "errors": []}

        # Single errors
        self.single_errors = ["error_ima_template",
                              "error_ima_template_wrong", 
                              "error_ima_template_download",
                              "error_ima_template_tab",
                              "error_ima_empty_data",
                              "error_ima_proc",
                              "error_ima_database",
                              "error_ima_database_IMA",
                              "error_ima_database_MEASURE",
                              "error_ima_file_name"
                              "error_ima_file_type",
                              "error_ima_file_format",
                              "error_ima_csv_wrong"]
        
        # Mult errors
        # "error_ima_required"
        # "error_ima_column"
        # "error_ima_source"
        # "error_ima_source_gauge"
        # "error_ima_quantity"

    def append_mult_error(self, line, error_type, error_param):

        # Se eh a primeira vez q o erro aparece na lista de erros
        if error_type not in self.mult_errors:
            self.mult_errors[error_type] = {}

        # Se o parametro ainda nao foi adicionado na listagem daquele erro
        if error_param not in self.mult_errors[error_type]:

            # Adiciona a linha como uma lista daquele parametro de erro
            # Ex: self.multi_errors[error_ima_column][Data] = [1]
            # Ex: self.multi_errors[error_ima_source][ARAXA] = [22]
            self.mult_errors[error_type][error_param] = [str(line)]
        else:
            # Se o parametro jah existe para aquele tipo de erro, entao apenas add a linha na lista
            # Ex: self.multi_errors[error_ima_source][ARAXA] = [22, 23, line]
            self.mult_errors[error_type][error_param].append(str(line))

        self._mult_errors = True

    def set_single_error(self, label_error):
        if label_error in self.single_errors:
            self.dic["msg"] = label_error
        else:
            self.dic["msg"] = "error_ima_unknown"
        self._single_errors = True

    def set_dic_response(self):

        # Se possui erros multiplos
        if self._mult_errors:
            
            # Pode conter erros unicos e erros multiplos ao mesmo tempo
            # Se houver apenas erros multiplos e não erros unicos
            if not self._single_errors:
                self.dic["msg"] = "success_ima_errors"

            # Precisamos transformar este formato:
            # self.multi_errors[error_ima_source][ARAXA] = [22, 23]

            # Para este formato
            # "errors": [
            #      {"error_type": "error_ima_source", "error_param": "ARAXA", "lines": '22,23'}
            # ]
            error_list = []
            for error_type in self.mult_errors:
                for error_param in self.mult_errors[error_type]:
                    lines = ','.join(self.mult_errors[error_type][error_param])
                    error_aux = {"error_type": error_type, "error_param": error_param, "lines": lines}
                    error_list.append(error_aux)

            self.dic["errors"] = error_list

        # Se possui erros unicos
        elif self._single_errors:
            #if self.dic["msg"] == "error_ima_proc":
                #self.mult_errors[error_type] = {}

            self.dic["errors"] = []

        # Se nao possui erros
        else:
            self.dic["msg"] = "success_ima"
            self.dic["errors"] = []

    def has_single_errors(self):
        return self._single_errors

    def has_multi_errors(self):
        return self._mult_errors

    def get_dic_response(self):
        self.set_dic_response()
        return self.dic


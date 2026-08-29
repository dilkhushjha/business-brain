from dataclasses import dataclass,field

@dataclass
class ImportReport:
    rows_read:int=0
    rows_accepted:int=0
    rows_rejected:int=0
    errors:list[str]=field(default_factory=list)

    @property
    def success(self)->bool:return self.rows_rejected==0

    def add_error(self,message:str)->None:
        self.rows_rejected+=1
        if len(self.errors)<25:self.errors.append(message)

    def as_dict(self)->dict:
        return {"rows_read":self.rows_read,"rows_accepted":self.rows_accepted,"rows_rejected":self.rows_rejected,"errors":self.errors,"success":self.success}

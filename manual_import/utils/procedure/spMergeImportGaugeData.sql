USE [SmartEnergy]
GO
/****** Object:  StoredProcedure [dbo].[spMergeImportGaugeData]    Script Date: 10/07/2020 14:54:00 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO

ALTER   procedure [dbo].[spMergeImportGaugeData] (
	@UTC_Creation datetime
) AS
BEGIN

begin try

	BEGIN TRAN

	-- Atualiza valor de registros que já existem na GUAGE_DATA
	UPDATE d	
		set d.UTC_CREATION = t.UTC_CREATION
		,	d.VALUE = t.VALUE
	FROM 
		dbo.GAUGE_DATA_TEMP t
	       inner join dbo.GAUGE_DATA d
		   on  t.ID_MEASUREMENTS  = d.ID_MEASUREMENTS
		   and t.ID_GAUGE         = d.ID_GAUGE
		   and t.UTC_GAUGE        = d.UTC_GAUGE
		   inner join dbo.IMPORT_SOURCE s
		   on d.ID_IMPORT_SOURCE = s.ID_IMPORT_SOURCE
	WHERE
		t.UTC_CREATION = @UTC_Creation
    and s.IMPORT_TYPE = 'Manual'

	-- Insere registros que ainda não existem na GUAGE_DATA
    INSERT INTO dbo.GAUGE_DATA (
			   ID_MEASUREMENTS
             , ID_IMPORT_SOURCE
             , ID_GAUGE
             , UTC_CREATION
             , UTC_GAUGE
             , VALUE
	)
    SELECT
	      t.ID_MEASUREMENTS
        , t.ID_IMPORT_SOURCE
        , t.ID_GAUGE
        , t.UTC_CREATION
        , t.UTC_GAUGE
        , t.VALUE
	FROM 
		dbo.GAUGE_DATA_TEMP t
	       left join dbo.GAUGE_DATA d
		   on  t.ID_MEASUREMENTS  = d.ID_MEASUREMENTS
		   and t.ID_GAUGE         = d.ID_GAUGE
		   and t.UTC_GAUGE        = d.UTC_GAUGE
	WHERE
		t.UTC_CREATION = @UTC_Creation
	and d.ID_GAUGE_DATA is null

	DELETE FROM dbo.GAUGE_DATA_TEMP where UTC_CREATION = @UTC_Creation

	COMMIT;

END TRY
BEGIN CATCH

	ROLLBACK;

	DELETE FROM dbo.GAUGE_DATA_TEMP where UTC_CREATION = @UTC_Creation

	DECLARE @ErrorMessage VARCHAR(4000);
    DECLARE @ErrorSeverity INT;
    DECLARE @ErrorState INT;

    SELECT 
        @ErrorMessage = ERROR_MESSAGE(),
        @ErrorSeverity = ERROR_SEVERITY(),
        @ErrorState = ERROR_STATE()

    RAISERROR (@ErrorMessage, @ErrorSeverity, @ErrorState);

END CATCH

END
go

